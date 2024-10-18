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
