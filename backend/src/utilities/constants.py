from enum import Enum


class ErrorMessages(Enum):
    PATIENT_EXISTS = "Patient already exists"
    DOCTOR_EXISTS = "Doctor already exists"
    ADMIN_EXISTS = "Admin already exists"
    INVALID_ROLE = "Invalid role specified"
    INVALID_CREDENTIALS = "Invalid credentials"
    LOGIN_ERROR = "Error logging in"
    PATIENT_NOT_FOUND = "Patient not found"
    DOCTOR_NOT_FOUND = "No doctors found for the given specialization"
    NO_DOCTORS_FOUND_FOR_SPECIALIZATION = (
        "No doctors found for the given specialization: '{}'"
    )
    NO_PATIENT_FOUND = "Patient not found with ID: {}"
    PATIENT_UPDATE_ERROR = "Error in updating the patient"
    DOCTOR_UPDATE_ERROR = "Error in updating the doctor"
    NO_DOCTOR_FOUND = "Doctor not found"
    TIMESLOT_CREATION_ERROR = "Error creating time slot"
    NO_AVAILABLE_TIMESLOTS = "No available time slots found for the doctor"
    TIMESLOT_NOT_FOUND = "Timeslot not found for doctor ID: {}"

    PRESCRIPTION_NOT_FOUND = "Prescription not found for ID: {}"
    NO_REMINDERS_FOUND = "No reminders found for prescription ID: {}"
    REMINDER_ACTIVATION_ERROR = "Unexpected error occurred while activating reminders"

    PRESCRIPTION_CREATION_ERROR = (
        "Internal server error occurred while creating the prescription."
    )
    PRESCRIPTION_UPDATE_ERROR = (
        "Internal server error occurred while updating the prescription."
    )
    PRESCRIPTION_DELETION_ERROR = (
        "Internal server error occurred while deleting the prescription."
    )

    INTERNAL_SERVER_ERROR = (
        "Internal server error occurred while processing your request."
    )
    APPOINTMENTS_FETCH_ERROR = "Error occurred while retrieving appointments."
    DOCTORS_FETCH_ERROR = "Error occurred while retrieving doctors."
    PATIENTS_FETCH_ERROR = "Error occurred while retrieving patients."

    TIME_SLOT_UNAVAILABLE = "The selected time slot is unavailable."
    APPOINTMENT_NOT_FOUND = "Appointment with ID {appointment_id} not found."
    NO_APPOINTMENTS_FOUND = "No appointments found for the specified doctor."
    PERMISSION_DENIED = (
        "You do not have permission to mark this appointment as inactive."
    )
    ERROR_BOOKING_APPOINTMENT = "Error booking the appointment."
    ERROR_RETRIEVING_APPOINTMENTS = "Error retrieving the doctor's appointments."
    UNEXPECTED_ERROR_MARKING_INACTIVE = (
        "Unexpected error occurred while marking appointment {appointment_id} inactive."
    )

    CHATBOT_FAILED_COMMUNICATION = "Failed to communicate with the chatbot."


class ChatbotResponses:
    NO_AVAILABLE_SLOTS = "Unfortunately, there are no available time slots for Dr. {doctor_name} at the moment. Let me find other doctors for you."
    OTHER_DOCTORS_AVAILABLE = "Here are other doctors you can choose from:\n{doctor_list}\n\nPlease enter the full name of the doctor you would like to select, or type 'reset' to start over."
    NO_OTHER_DOCTORS = "Unfortunately, there are no other doctors available at the moment. You can type 'reset' or 'start over' at any time to begin a new conversation."
    AVAILABLE_SLOTS = "Here are the available time slots for Dr. {doctor_name}:\n\n{slots_list}\n\nPlease enter the number corresponding to the slot you would like to book. You can also type 'reset' or 'start over' at any time to begin a new conversation."
    DOCTOR_NOT_FOUND = "I couldn't find the doctor you mentioned. Please enter the full name of the doctor you want to select, or type 'reset' to ask another question."
    RESET_OPTION = "You can type 'reset' or 'start over' at any time to begin a new conversation."


    APPOINTMENT_BOOKED = (
        "Your appointment with Dr. {doctor_name} has been successfully booked for {start_time} - {end_time}. \n\n"
        "You can ask any time about your prescription. If prescriptions are available, I can help you activate medication reminders. "
        "If no prescriptions are entered yet, I'll let you know.\n"
        "You can type 'reset' or 'start over' at any time to begin a new conversation."
    )
    INVALID_SLOT_SELECTION = (
        "The selected time slot is not available. Please enter a valid number corresponding to the slot, "
        "or type 'reset' to start over."
    )
    INVALID_INPUT = (
        "Invalid input. Please enter a valid number corresponding to the time slot, "
        "or type 'reset' to start over."
    )


    PRESCRIPTIONS_FOUND = (
        "I found the following prescriptions:\n{prescription_list}\n"
        "Would you like to activate reminders for any of them? (Yes/No)"
    )
    ALL_REMINDERS_ACTIVE = "All your active prescriptions already have active reminders."
    NO_NEW_PRESCRIPTIONS = "It appears that your doctor hasn't entered any new prescriptions for you at the moment."
    NO_PRESCRIPTIONS = "It appears that your doctor hasn't entered any prescriptions for you at the moment."


    CONFIRM_EXIT = "Understood. Is there anything else I can help you with?"
    UNRECOGNIZED_RESPONSE = (
        "I'm sorry, I didn't understand that. If you're done, you can say 'okay' or 'exit'. "
        "Is there anything else I can help you with?"
    )


    REMINDERS_ACTIVATED = (
        "Reminders for {medication_name} have been activated for: {reminder_times}.\n"
        "Would you like to update the reminder times? (Yes/No)"
    )
    ISSUE_ACTIVATING = (
        "I'm sorry, there was an issue activating your reminders for {medication_name}: {error_detail}"
    )
    NEXT_PRESCRIPTION_PROMPT = (
        "Next prescription: {medication_name}. "
        "Would you like to activate reminders for this prescription? (Yes/No)"
    )
    ALL_REMINDERS_ACTIVE = "All reminders have already been activated."
    NO_REMINDERS_ACTIVATED = "No reminders have been activated."


    REQUEST_NEW_TIMES = (
        "Please provide the new times for your reminders. You can specify them in the format 'HH:MM AM/PM', "
        "separated by commas. For example: '09:00 AM, 01:00 PM, 06:00 PM'."
    )
    NEXT_PRESCRIPTION_PROMPT = (
        "Next prescription: {medication_name}. Would you like to activate reminders for this prescription? (Yes/No)"
    )
    ALL_PRESCRIPTIONS_PROCESSED = "All prescriptions have been processed."
    UNRECOGNIZED_RESPONSE = "I didn't understand that. Please answer with 'Yes' or 'No'."
    EXIT_UNRECOGNIZED_RESPONSE = "I didn't understand that. Please answer with 'ok' or 'exit'."


    UPDATE_SUCCESS = (
        "Reminder times have been updated to: {formatted_times} (24-hour format).\n\n"
        "Next prescription: {medication_name}. Would you like to activate reminders for this prescription? (Yes/No)"
    )
    ALL_PRESCRIPTIONS_PROCESSED = "Reminder times have been updated to: {formatted_times}.\nAll prescriptions have been processed."
    FINDING_PRESCRIPTION_ERROR = "Sorry, there was an issue finding your prescription."
    PROCESSING_ERROR = "There was an error processing the new times. Please try again using the format 'HH:MM AM/PM'."


class GenderEnum(Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class BloodGroupEnum(Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
