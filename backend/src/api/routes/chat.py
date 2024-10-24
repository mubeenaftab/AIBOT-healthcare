from typing import Any, Dict, List, Union

import pendulum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.routes.appointment import book_appointment
from src.api.routes.doctor import get_doctors_by_specialization
from src.api.routes.reminder import activate_reminders_for_prescription
from src.api.routes.timeslot import get_available_time_slots
from src.config.settings.logger_config import logger
from src.models.db.user import Patient as PatientModel
from src.models.schemas.appointment import AppointmentCreate
from src.models.schemas.chatbot import ChatQuery, ChatResponse
from src.models.schemas.doctor import DoctorResponse
from src.models.schemas.error_response import ErrorResponse
from src.repository.crud.appointment import get_inactive_appointment
from src.repository.crud.chat import get_chatbot_response, reminder_queue
from src.repository.crud.prescription import (
    get_inactive_prescriptions_without_active_reminders,
    get_prescriptions_for_appointment,
    mark_prescription_inactive,
)
from src.repository.crud.reminder import update_reminder_times
from src.repository.crud.timeslot import update_time_slot_with_patient
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user
from src.utilities.constants import ChatbotResponses, ErrorMessages

router = APIRouter()


conversation_state: Dict[str, Any] = {
    "stage": "initial",
    "doctors": [],
}


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def chat_with_bot(
    query: ChatQuery,
    db: AsyncSession = Depends(get_db),
    current_user: PatientModel = Depends(get_current_user),
) -> Union[ChatResponse, HTTPException]:
    """
    Handle conversation with the chatbot, including doctor selection and appointment booking.

    Args:
        query (ChatQuery): The user's message and associated query.
        db (AsyncSession): The database session.

    Returns:
        ChatResponse: The response from the chatbot, which may include available doctors or appointment confirmation.

    Raises:
        HTTPException: If there's an error during the processing of the chat, including database access errors.
    """
    logger.debug(f"Current user: {current_user}")

    user_message = query.user_message.strip().lower()
    logger.info(f"Received message: {user_message}")

    # Check if current_user is properly resolved
    if current_user is None or not hasattr(current_user, "user_id"):
        logger.error("Current user is not properly resolved")
        raise HTTPException(status_code=401, detail="Could not authenticate user")

    patient_id = current_user.user_id
    logger.debug(f"patient_id: {patient_id}")

    # Check if the user wants to reset the conversation
    if user_message in ["reset", "start over"]:
        conversation_state["stage"] = "general"
        conversation_state.pop("doctors", None)
        conversation_state.pop("selected_doctor", None)
        conversation_state.pop("appointment_id", None)
        return ChatResponse(
            response="The conversation has been reset. You can start by asking a new question.",
        )

    try:
        # Stage 1: Handling doctor selection
        if conversation_state["stage"] == "awaiting_doctor_selection":
            return await handle_doctor_selection(user_message, db)
        # Stage 2: Handling time slot selection
        elif conversation_state["stage"] == "awaiting_slot_selection":
            return await handle_slot_selection(user_message, db, patient_id)
        # Stage 3: Checking for Inactive Prescriptions
        elif conversation_state["stage"] == "check_inactive_appointments":
            return await check_inactive_appointments(db, patient_id)
        # Stage 4: Handle exit keywords
        elif conversation_state["stage"] == "waiting_for_exit":
            return await handle_exit_responses(user_message)
        # Stage 5: Activate Reminders and Ask for Update
        elif conversation_state["stage"] == "activate_reminders":
            return await handle_activate_reminders(user_message, db)
        # Stage 6: Ask if the user wants to update reminder times
        elif conversation_state["stage"] == "update_reminder_prompt":
            return await handle_update_reminders(user_message)
        # Stage 7: Collect and Update Reminder Times
        elif conversation_state["stage"] == "collect_new_reminder_times":
            return await collect_new_reminder_times(user_message, db)
        # Default: Handle general conversation and suggest doctors if needed
        chatbot_response = await get_chatbot_response(user_message)

        if chatbot_response.get("suggest_doctor"):
            specialization = chatbot_response["specialization"]
            try:
                doctors_response = await get_doctors_by_specialization(
                    specialization, db
                )

                if not doctors_response:
                    return ChatResponse(
                        response=f"{chatbot_response['response']} However, no doctors were found for the specialization: {specialization}. You can type 'reset' or 'start over' to begin a new conversation.",
                    )
            except HTTPException as e:
                logger.error(f"Error fetching doctors: {e.detail}")
                return ChatResponse(
                    response=f"{chatbot_response['response']} Unfortunately, no doctors are available at the moment for your concerns. Please consult a healthcare professional if needed.",
                )

            doctor_list = "\n".join(
                [
                    f"Dr. {doctor.first_name} {doctor.last_name} ({doctor.specialization}) | Experience: {doctor.years_of_experience} years | Fees: Rs.{doctor.consultation_fee}"
                    for doctor in doctors_response
                ]
            )
            conversation_state["stage"] = "awaiting_doctor_selection"
            conversation_state["doctors"] = doctors_response

            return ChatResponse(
                response=(
                    f"{chatbot_response['response']}\n\n"
                    f"Here are the available doctors:\n{doctor_list}\n\n"
                    "Please enter the full name of the doctor you want to select, or type 'reset' to start a new conversation."
                ),
                doctors=[
                    DoctorResponse(
                        first_name=doctor.first_name,
                        last_name=doctor.last_name,
                        specialization=doctor.specialization,
                        years_of_experience=doctor.years_of_experience,
                        consultation_fee=doctor.consultation_fee,
                    )
                    for doctor in doctors_response
                ],
            )
        elif chatbot_response.get("check_prescriptions"):
            conversation_state["stage"] = "check_inactive_appointments"
            return await chat_with_bot(query, db, current_user)
        else:
            return ChatResponse(
                response=chatbot_response["response"]
                + " You can type 'reset' or 'start over' to begin a new conversation.",
            )

    except Exception as e:
        logger.error(f"Error during chatbot response: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorMessages.CHATBOT_FAILED_COMMUNICATION.value,
        ) from e


async def handle_doctor_selection(user_message: str, db: AsyncSession) -> ChatResponse:
    """
    Handle the selection of a doctor based on user input and check for available time slots.

    Args:
        user_message (str): The name of the doctor selected by the user.
        db (AsyncSession): The database session to execute queries.

    Returns:
        ChatResponse: The response to be sent to the user, either confirming the slot selection or providing alternative options.
    """
    selected_doctor_name = user_message.lower()

    for doctor in conversation_state["doctors"]:
        full_name = f"{doctor.first_name} {doctor.last_name}".lower()

        if selected_doctor_name == full_name:
            doctor_id = doctor.user_id
            available_slots = await get_available_time_slots(doctor_id, db)
            logger.debug("available_slots: %s", available_slots)

            if not available_slots:
                no_slots_response = ChatbotResponses.NO_AVAILABLE_SLOTS.format(
                    doctor_name=f"{doctor.first_name} {doctor.last_name}"
                )

                other_doctors_with_slots = [
                    doc
                    for doc in conversation_state["doctors"]
                    if doc.user_id != doctor_id
                    and await get_available_time_slots(doc.user_id, db)
                ]

                if other_doctors_with_slots:
                    doctor_list = "\n".join(
                        [
                            f"Dr. {doc.first_name} {doc.last_name}"
                            for doc in other_doctors_with_slots
                        ]
                    )
                    return ChatResponse(
                        response=(
                            f"{no_slots_response}\n\n"
                            f"{ChatbotResponses.OTHER_DOCTORS_AVAILABLE.format(doctor_list=doctor_list)}"
                        ),
                    )
                else:
                    return ChatResponse(
                        response=(
                            f"{no_slots_response}\n\n"
                            f"{ChatbotResponses.NO_OTHER_DOCTORS}"
                        ),
                    )

            slots_list = "\n".join(
                [
                    f"{i + 1}. {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
                    for i, slot in enumerate(available_slots)
                ]
            )
            conversation_state["stage"] = "awaiting_slot_selection"
            conversation_state["selected_doctor"] = doctor

            return ChatResponse(
                response=ChatbotResponses.AVAILABLE_SLOTS.format(
                    doctor_name=f"{doctor.first_name} {doctor.last_name}",
                    slots_list=slots_list,
                ),
            )

    return ChatResponse(
        response=ChatbotResponses.DOCTOR_NOT_FOUND,
    )


async def handle_slot_selection(
    user_message: str, db: AsyncSession, patient_id: int
) -> ChatResponse:
    """
    Handles the user's selection of a time slot for an appointment.

    Args:
        user_message (str): The user's input, which should be a number representing the slot index.
        db (AsyncSession): The database session to use for querying and updates.
        patient_id (int): The ID of the patient booking the appointment.

    Returns:
        ChatResponse: A response to the user about the appointment booking status.
    """
    try:
        selected_slot_index = int(user_message) - 1

        available_slots = await get_available_time_slots(
            conversation_state["selected_doctor"].user_id, db
        )

        if 0 <= selected_slot_index < len(available_slots):
            selected_slot = available_slots[selected_slot_index]

            updated_slot = await update_time_slot_with_patient(
                db=db,
                time_slot_id=selected_slot.time_slot_id,
                patient_id=patient_id,
            )

            # Create appointment if needed
            current_date = pendulum.now().date()
            appointment_data = AppointmentCreate(
                doctor_id=conversation_state["selected_doctor"].user_id,
                time_slot_id=updated_slot.time_slot_id,
                patient_id=patient_id,
                appointment_date=current_date,
            )
            await book_appointment(appointment_data, db)

            conversation_state["stage"] = "general"

            return ChatResponse(
                response=ChatbotResponses.APPOINTMENT_BOOKED.format(
                    doctor_name=f"{conversation_state['selected_doctor'].first_name} {conversation_state['selected_doctor'].last_name}",
                    start_time=selected_slot.start_time.strftime("%I:%M %p"),
                    end_time=selected_slot.end_time.strftime("%I:%M %p"),
                    email=f"{conversation_state['selected_doctor'].email}",
                ),
            )
        else:
            return ChatResponse(
                response=ChatbotResponses.INVALID_SLOT_SELECTION,
            )

    except ValueError:
        return ChatResponse(
            response=ChatbotResponses.INVALID_INPUT,
        )


async def check_inactive_appointments(
    db: AsyncSession, patient_id: int
) -> ChatResponse:
    """
    Check for inactive appointments and prescriptions and handle conversation state.

    Args:
        db (AsyncSession): The database session to execute queries.
        patient_id (int): The ID of the patient.

    Returns:
        ChatResponse: The chatbot response based on the current state.
    """
    inactive_appointment = await get_inactive_appointment(db, patient_id)

    if inactive_appointment:
        prescriptions = await get_prescriptions_for_appointment(
            db, inactive_appointment.patient_id, inactive_appointment.doctor_id
        )

        if prescriptions:
            inactive_prescriptions = (
                await get_inactive_prescriptions_without_active_reminders(
                    db, prescriptions
                )
            )

            if inactive_prescriptions:
                conversation_state["stage"] = "activate_reminders"
                conversation_state["prescriptions"] = [
                    {"prescription_id": p.prescription_id, "details": p.medication_name}
                    for p in inactive_prescriptions
                ]
                prescription_list = "\n".join(
                    f"{idx + 1}. {p.medication_name}"
                    for idx, p in enumerate(inactive_prescriptions)
                )
                return ChatResponse(
                    response=ChatbotResponses.PRESCRIPTIONS_FOUND.format(
                        prescription_list=prescription_list
                    )
                )
            else:
                conversation_state["stage"] = "waiting_for_exit"
                return ChatResponse(response=ChatbotResponses.ALL_REMINDERS_ACTIVE)
        else:
            conversation_state["stage"] = "waiting_for_exit"
            return ChatResponse(response=ChatbotResponses.NO_NEW_PRESCRIPTIONS)
    else:
        conversation_state["stage"] = "waiting_for_exit"
        return ChatResponse(response=ChatbotResponses.NO_PRESCRIPTIONS)


async def handle_exit_responses(user_message: str) -> ChatResponse:
    """
    Handle responses for ending the conversation.

    Args:
        user_message (str): The user's message.

    Returns:
        ChatResponse: The response to confirm exit or ask for clarification.
    """
    if user_message.lower() in ["ok", "okay", "fine", "thanks", "exit", "no"]:
        conversation_state.clear()
        conversation_state["stage"] = "reset"
        return ChatResponse(response=ChatbotResponses.CONFIRM_EXIT)
    else:
        return ChatResponse(response=ChatbotResponses.EXIT_UNRECOGNIZED_RESPONSE)


async def handle_activate_reminders(
    user_message: str, db: AsyncSession
) -> ChatResponse:
    """
    Activate prescription reminders based on user confirmation.

    Args:
        user_message (str): The user's response indicating whether to activate reminders.
        db (AsyncSession): The database session to execute queries.

    Returns:
        ChatResponse: The response to be sent to the user regarding the activation of reminders.
    """
    affirmative_responses = {"yes", "yeah", "yup", "sure", "ok", "alright", "go ahead"}

    if user_message.lower() in affirmative_responses:
        if conversation_state["prescriptions"]:
            current_prescription = conversation_state["prescriptions"].pop(0)
            prescription_id = current_prescription["prescription_id"]
            medication_name = current_prescription["details"]

            logger.debug(
                f"Activating reminders for prescription: {prescription_id}, medication: {medication_name}"
            )

            try:
                activated_reminders = await activate_reminders_for_prescription(
                    prescription_id, db
                )

                unique_reminder_times = []
                for reminder in activated_reminders:
                    time_str = reminder.reminder_time.strftime("%I:%M %p")
                    if time_str not in unique_reminder_times:
                        unique_reminder_times.append(time_str)

                reminder_times = ", ".join(unique_reminder_times)

                # Mark the prescription as inactive
                updated_prescription = await mark_prescription_inactive(
                    db, prescription_id
                )

                if updated_prescription is None:
                    logger.warning(
                        f"Failed to mark prescription {prescription_id} as inactive"
                    )
                else:
                    logger.info(f"Prescription {prescription_id} marked as inactive")

                conversation_state["stage"] = "update_reminder_prompt"
                conversation_state["prescription_id"] = prescription_id
                return ChatResponse(
                    response=ChatbotResponses.REMINDERS_ACTIVATED.format(
                        medication_name=medication_name, reminder_times=reminder_times
                    )
                )
            except HTTPException as e:
                conversation_state["stage"] = "general"
                return ChatResponse(
                    response=ChatbotResponses.ISSUE_ACTIVATING.format(
                        medication_name=medication_name, error_detail=e.detail
                    )
                )
        else:
            if conversation_state["prescriptions"]:
                current_prescription = conversation_state["prescriptions"][0]
                medication_name = current_prescription["details"]
                return ChatResponse(
                    response=ChatbotResponses.NEXT_PRESCRIPTION_PROMPT.format(
                        medication_name=medication_name
                    )
                )
            else:
                conversation_state["stage"] = "general"
                return ChatResponse(response=ChatbotResponses.ALL_REMINDERS_ACTIVE)

    return ChatResponse(response=ChatbotResponses.NO_REMINDERS_ACTIVATED)


async def handle_update_reminders(user_message: str) -> ChatResponse:
    """
    Update the times for prescription reminders.

    Args:
        user_message (str): The user's message.

    Returns:
        ChatResponse: The chatbot's response regarding updating reminder times.
    """
    affirmative_responses = {"yes", "yeah", "yup", "sure", "ok", "alright", "go ahead"}
    negative_responses = {"no", "nope", "not now", "nah", "never mind"}

    if user_message.lower() in affirmative_responses:
        conversation_state["stage"] = "collect_new_reminder_times"
        return ChatResponse(response=ChatbotResponses.REQUEST_NEW_TIMES)
    elif user_message.lower() in negative_responses:
        if conversation_state.get("prescriptions"):
            current_prescription = conversation_state["prescriptions"][0]
            medication_name = current_prescription["details"]
            conversation_state["stage"] = "activate_reminders"
            return ChatResponse(
                response=ChatbotResponses.NEXT_PRESCRIPTION_PROMPT.format(
                    medication_name=medication_name
                )
            )
        else:
            conversation_state["stage"] = "general"
            return ChatResponse(response=ChatbotResponses.ALL_PRESCRIPTIONS_PROCESSED)
    else:
        return ChatResponse(response=ChatbotResponses.UNRECOGNIZED_RESPONSE)


async def collect_new_reminder_times(
    user_message: str, db: AsyncSession
) -> ChatResponse:
    """
    Collect and update new reminder times for a prescription based on user input.

    Args:
        user_message (str): The user's input containing new reminder times separated by commas.
        db (AsyncSession): The database session to execute queries.

    Returns:
        ChatResponse: The response to be sent to the user regarding the update of reminder times.
    """
    try:
        new_times_str = user_message.split(",")
        new_times = []

        for time_str in new_times_str:
            parsed_time = pendulum.parse(time_str.strip(), strict=False)
            new_times.append({"hour": parsed_time.hour, "minute": parsed_time.minute})

        prescription_id = conversation_state.get("prescription_id")
        if prescription_id:
            await update_reminder_times(prescription_id, new_times, db)

            formatted_times = [
                f"{time['hour']:02}:{time['minute']:02}" for time in new_times
            ]

            if conversation_state["prescriptions"]:
                current_prescription = conversation_state["prescriptions"][0]
                medication_name = current_prescription["details"]
                conversation_state["stage"] = "activate_reminders"
                return ChatResponse(
                    response=ChatbotResponses.UPDATE_SUCCESS.format(
                        formatted_times=", ".join(formatted_times),
                        medication_name=medication_name,
                    )
                )
            else:
                conversation_state["stage"] = "general"
                return ChatResponse(
                    response=ChatbotResponses.ALL_PRESCRIPTIONS_PROCESSED.format(
                        formatted_times=", ".join(formatted_times)
                    )
                )
        else:
            conversation_state["stage"] = "general"
            return ChatResponse(response=ChatbotResponses.FINDING_PRESCRIPTION_ERROR)
    except Exception as e:
        logger.error(f"Error parsing new reminder times: {e}")
        return ChatResponse(response=ChatbotResponses.PROCESSING_ERROR)


@router.get("/chat/reminders", response_class=JSONResponse)
async def get_reminders() -> JSONResponse:
    """
    Retrieve reminders from the reminder queue.

    This endpoint fetches all reminders currently in the reminder queue.
    It extracts reminders from the queue until it is empty and returns them as a list.

    Returns:
        JSONResponse: A JSON response containing a list of reminders.
    """
    reminders: List[str] = []
    while not reminder_queue.empty():
        reminders.append(reminder_queue.get())
    return JSONResponse(content={"reminders": reminders})
