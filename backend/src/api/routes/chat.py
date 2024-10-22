from typing import Any, Dict, List, Union

import pendulum
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.api.routes.reminder import activate_reminders_for_prescription
from src.api.routes.timeslot import get_available_time_slots
from src.api.routes.user import get_doctors_by_specialization
from src.config.settings.logger_config import logger
from src.models.db.appointment import Appointment as AppointmentModel
from src.models.db.prescription import Prescription as PrescriptionModel
from src.models.db.reminder import Reminder as ReminderModel
from src.models.db.user import Patient as PatientModel
from src.models.schemas.chatbot import ChatQuery, ChatResponse
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.reminder import ReminderStatus
from src.models.schemas.user import DoctorResponse
from src.repository.crud.chat import get_chatbot_response, reminder_queue
from src.repository.crud.prescription import mark_prescription_inactive
from src.repository.crud.reminder import update_reminder_times
from src.repository.crud.timeslot import update_time_slot_with_patient
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user
from src.utilities.constants import ErrorMessages

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
            selected_doctor_name = user_message
            for doctor in conversation_state["doctors"]:
                full_name = f"{doctor.first_name} {doctor.last_name}".lower()
                if selected_doctor_name == full_name:
                    doctor_id = doctor.user_id
                    available_slots = await get_available_time_slots(doctor_id, db)
                    logger.debug("available_slots ", available_slots)
                    if not available_slots:
                        # Inform user that the selected doctor has no available slots
                        no_slots_response = (
                            f"Unfortunately, there are no available time slots for Dr. {doctor.first_name} {doctor.last_name} at the moment. "
                            "Let me find other doctors for you."
                        )

                        # Get a list of other doctors who do have available time slots
                        other_doctors_with_slots = []
                        for doc in conversation_state["doctors"]:
                            if doc.user_id != doctor_id:
                                other_available_slots = await get_available_time_slots(
                                    doc.user_id, db
                                )
                                if other_available_slots:
                                    other_doctors_with_slots.append(doc)

                        if other_doctors_with_slots:
                            # Create a list of doctors with available slots
                            doctor_list = "\n".join(
                                [
                                    f"Dr. {doc.first_name} {doc.last_name}"
                                    for doc in other_doctors_with_slots
                                ]
                            )
                            return ChatResponse(
                                response=(
                                    f"{no_slots_response}\n\n"
                                    f"Here are other doctors you can choose from:\n{doctor_list}\n\n"
                                    "Please enter the full name of the doctor you would like to select, or type 'reset' to start over."
                                ),
                            )
                        else:
                            return ChatResponse(
                                response=(
                                    f"{no_slots_response}\n\n"
                                    "Unfortunately, there are no other doctors available at the moment. "
                                    "You can type 'reset' or 'start over' at any time to begin a new conversation."
                                ),
                            )

                    # If there are available slots, proceed as normal
                    slots_list = "\n".join(
                        [
                            f"{i + 1}. {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
                            for i, slot in enumerate(available_slots)
                        ]
                    )
                    conversation_state["stage"] = "awaiting_slot_selection"
                    conversation_state["selected_doctor"] = doctor

                    return ChatResponse(
                        response=(
                            f"Here are the available time slots for Dr. {doctor.first_name} {doctor.last_name}:\n\n"
                            f"{slots_list}\n\n"
                            "Please enter the number corresponding to the slot you would like to book. "
                            "You can also type 'reset' or 'start over' at any time to begin a new conversation."
                        ),
                    )

            return ChatResponse(
                response="I couldn't find the doctor you mentioned. Please enter the full name of the doctor you want to select, or type 'reset' to ask another question.",
            )

        # Stage 2: Handling time slot selection
        elif conversation_state["stage"] == "awaiting_slot_selection":
            try:
                slot_number = int(user_message)
                available_slots = await get_available_time_slots(
                    conversation_state["selected_doctor"].user_id, db
                )

                if not (1 <= slot_number <= len(available_slots)):
                    return ChatResponse(
                        response="Invalid slot number. Please select a valid number from the list."
                    )

                selected_slot = available_slots[slot_number - 1]

                # Update the time slot with patient information
                try:
                    updated_slot = await update_time_slot_with_patient(
                        db=db,
                        time_slot_id=selected_slot.time_slot_id,
                        patient_id=patient_id,
                    )

                    # Reset conversation state
                    conversation_state["stage"] = "booking_confirmed"

                    return ChatResponse(
                        response=(
                            f"Great! I've booked your appointment with "
                            f"Dr. {conversation_state['selected_doctor'].first_name} "
                            f"{conversation_state['selected_doctor'].last_name} for "
                            f"{updated_slot.start_time.strftime('%I:%M %p')} - "
                            f"{updated_slot.end_time.strftime('%I:%M %p')}. "
                            "You'll receive a confirmation shortly."
                        )
                    )

                except ValueError as ve:
                    logger.error(f"Booking error: {ve}")
                    return ChatResponse(
                        response="Sorry, this time slot is no longer available. Please select a different time slot."
                    )

            except ValueError:
                return ChatResponse(
                    response="Please enter a valid number corresponding to the time slot you want to book."
                )

        # Stage 3: Checking for Inactive Prescriptions
        elif conversation_state["stage"] == "check_inactive_appointments":
            inactive_appointments = await db.execute(
                select(AppointmentModel)
                .where(AppointmentModel.patient_id == patient_id)
                .where(AppointmentModel.is_active.is_(False))
                .order_by(AppointmentModel.appointment_date.desc())
            )
            inactive_appointment = inactive_appointments.scalars().first()
            logger.debug(f"inactive_appointment: {inactive_appointment}")

            if inactive_appointment:
                prescriptions = await db.execute(
                    select(PrescriptionModel)
                    .where(
                        PrescriptionModel.patient_id == inactive_appointment.patient_id
                    )
                    .where(
                        PrescriptionModel.doctor_id == inactive_appointment.doctor_id
                    )
                )
                prescriptions = prescriptions.scalars().all()

                if prescriptions:
                    inactive_prescriptions = []
                    for prescription in prescriptions:
                        if prescription.is_active:
                            active_reminders = await db.execute(
                                select(ReminderModel)
                                .where(
                                    ReminderModel.prescription_id
                                    == prescription.prescription_id
                                )
                                .where(ReminderModel.status == ReminderStatus.ACTIVE)
                            )
                            if not active_reminders.scalars().first():
                                inactive_prescriptions.append(prescription)

                    if inactive_prescriptions:
                        conversation_state["stage"] = "activate_reminders"
                        conversation_state["prescriptions"] = [
                            {
                                "prescription_id": p.prescription_id,
                                "details": p.medication_name,
                            }
                            for p in inactive_prescriptions
                        ]
                        prescription_list = "\n".join(
                            f"{idx + 1}. {p.medication_name}"
                            for idx, p in enumerate(inactive_prescriptions)
                        )
                        return ChatResponse(
                            response=f"I found the following prescriptions:\n{prescription_list}\n"
                            "Would you like to activate reminders for any of them? (Yes/No)"
                        )
                    else:
                        conversation_state["stage"] = "waiting_for_exit"
                        return ChatResponse(
                            response="All your active prescriptions already have active reminders."
                        )
                else:
                    conversation_state["stage"] = "waiting_for_exit"
                    return ChatResponse(
                        response="It appears that your doctor hasn't entered any new prescriptions for you at the moment."
                    )
            else:
                conversation_state["stage"] = "waiting_for_exit"
                return ChatResponse(
                    response="It appears that your doctor hasn't entered any prescriptions for you at the moment."
                )

        # Stage 4: Handle exit keywords
        elif conversation_state["stage"] == "waiting_for_exit":
            if user_message.lower() in ["ok", "okay", "fine", "thanks", "exit", "no"]:
                conversation_state["stage"] = "reset"
                return ChatResponse(
                    response="Understood. Is there anything else I can help you with?",
                )
            else:
                return ChatResponse(
                    response="I'm sorry, I didn't understand that. If you're done, you can say 'okay' or 'exit'. Is there anything else I can help you with?",
                )

        # Stage 5: Activate Reminders and Ask for Update
        elif conversation_state["stage"] == "activate_reminders":
            affirmative_responses = {
                "yes",
                "yeah",
                "yup",
                "sure",
                "ok",
                "alright",
                "go ahead",
            }
            negative_responses = {"no", "nope", "not now", "nah", "never mind"}

            if user_message.lower() in affirmative_responses:
                if conversation_state["prescriptions"]:
                    current_prescription = conversation_state["prescriptions"].pop(
                        0
                    )  # Remove the first prescription
                    prescription_id = current_prescription["prescription_id"]
                    medication_name = current_prescription["details"]

                    logger.debug(
                        f"Activating reminders for prescription: {prescription_id}, medication: {medication_name}"
                    )

                    try:
                        activated_reminders = await activate_reminders_for_prescription(
                            prescription_id, db
                        )
                        reminder_times = ", ".join(
                            [
                                r.reminder_time.strftime("%I:%M %p")
                                for r in activated_reminders
                            ]
                        )

                        # Mark the prescription as inactive
                        updated_prescription = await mark_prescription_inactive(
                            db, prescription_id
                        )

                        if updated_prescription is None:
                            logger.warning(
                                f"Failed to mark prescription {prescription_id} as inactive"
                            )
                        else:
                            logger.info(
                                f"Prescription {prescription_id} marked as inactive"
                            )

                        # Ask user if they want to change reminder times
                        conversation_state["stage"] = "update_reminder_prompt"
                        conversation_state["prescription_id"] = prescription_id
                        return ChatResponse(
                            response=f"Reminders for {medication_name} have been activated for: {reminder_times}. "
                            f"The prescription has been marked as inactive. "
                            f"Would you like to update the reminder times? (Yes/No)"
                        )
                    except HTTPException as e:
                        conversation_state["stage"] = "general"
                        return ChatResponse(
                            response=f"I'm sorry, there was an issue activating your reminders for {medication_name}: {e.detail}",
                        )
                else:
                    # Check if there are more prescriptions to process
                    if conversation_state["prescriptions"]:
                        # Continue to the next prescription
                        current_prescription = conversation_state["prescriptions"][0]
                        medication_name = current_prescription["details"]
                        return ChatResponse(
                            response=f"Next prescription: {medication_name}. Would you like to activate reminders for this prescription? (Yes/No)"
                        )
                    else:
                        # If no more prescriptions, go back to the general state
                        conversation_state["stage"] = "general"
                        return ChatResponse(
                            response="All reminders have already been activated."
                        )

        # Stage 6: Ask if the user wants to update reminder times
        elif conversation_state["stage"] == "update_reminder_prompt":
            affirmative_responses = {
                "yes",
                "yeah",
                "yup",
                "sure",
                "ok",
                "alright",
                "go ahead",
            }
            negative_responses = {"no", "nope", "not now", "nah", "never mind"}

            if user_message.lower() in affirmative_responses:
                # Ask the user for new reminder times
                conversation_state["stage"] = "collect_new_reminder_times"
                return ChatResponse(
                    response="Please provide the new times for your reminders. You can specify them in the format 'HH:MM AM/PM', separated by commas. For example: '09:00 AM, 01:00 PM, 06:00 PM'."
                )
            elif user_message.lower() in negative_responses:
                # Check if there are more prescriptions to process instead of going to general stage
                if conversation_state["prescriptions"]:
                    # Continue to the next prescription
                    current_prescription = conversation_state["prescriptions"][0]
                    medication_name = current_prescription["details"]
                    conversation_state["stage"] = (
                        "activate_reminders"  # Set stage back to activate_reminders
                    )
                    return ChatResponse(
                        response=f"Next prescription: {medication_name}. Would you like to activate reminders for this prescription? (Yes/No)"
                    )
                else:
                    # Only go to general stage if no more prescriptions
                    conversation_state["stage"] = "general"
                    return ChatResponse(
                        response="All prescriptions have been processed.",
                    )
            else:
                return ChatResponse(
                    response="I didn't understand that. Please answer with 'Yes' or 'No'.",
                )

        # Stage 7: Collect and Update Reminder Times
        elif conversation_state["stage"] == "collect_new_reminder_times":
            try:
                new_times_str = user_message.split(",")
                new_times = []

                for time_str in new_times_str:
                    parsed_time = pendulum.parse(time_str.strip(), strict=False)
                    new_times.append(
                        {"hour": parsed_time.hour, "minute": parsed_time.minute}
                    )

                # Call function to update the reminder times
                prescription_id = conversation_state.get("prescription_id")
                if prescription_id:
                    await update_reminder_times(prescription_id, new_times, db)

                    # Manually format the times to display them
                    formatted_times = [
                        f"{time['hour']:02}:{time['minute']:02}" for time in new_times
                    ]

                    # Check for more prescriptions instead of going to general stage
                    if conversation_state["prescriptions"]:
                        current_prescription = conversation_state["prescriptions"][0]
                        medication_name = current_prescription["details"]
                        conversation_state["stage"] = "activate_reminders"
                        return ChatResponse(
                            response=f"Reminder times have been updated to: {', '.join(formatted_times)}.\n\n"
                            f"Next prescription: {medication_name}. Would you like to activate reminders for this prescription? (Yes/No)"
                        )
                    else:
                        conversation_state["stage"] = "general"
                        return ChatResponse(
                            response=f"Reminder times have been updated to: {', '.join(formatted_times)}.\n"
                            f"All prescriptions have been processed."
                        )
                else:
                    conversation_state["stage"] = "general"
                    return ChatResponse(
                        response="Sorry, there was an issue finding your prescription."
                    )
            except Exception as e:
                logger.error(f"Error parsing new reminder times: {e}")
                return ChatResponse(
                    response="There was an error processing the new times. Please try again using the format 'HH:MM AM/PM'."
                )

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
                    f"Dr. {doctor.first_name} {doctor.last_name} ({doctor.specialization})"
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


@router.get("/chat/reminders")
async def get_reminders():
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
