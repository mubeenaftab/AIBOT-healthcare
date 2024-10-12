"""
Imports for handling appointment-related functionality in the FastAPI application.
Includes routing, dependency management, and database interactions.

- APIRouter: Facilitates the creation of API routes.
- Depends: Enables dependency injection for request handling.
- HTTPException: Exception class for returning HTTP error responses.
- status: Contains HTTP status codes.
- AsyncSession: Asynchronous database session management for SQLAlchemy.
- logger: Application logging configuration.
- Appointment, AppointmentCreate: Pydantic schemas for appointment data handling.
- ErrorResponse: Schema for standardized error responses.
- create_appointment, get_time_slot_by_id_from_db, update_time_slot_status: CRUD functions for appointment management.
- get_db: Dependency to obtain a database session.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.db.user import Doctor

from src.models.schemas.appointment import (
    Appointment,
    AppointmentCreate,
    PagedAppointment,
)

from src.models.schemas.error_response import ErrorResponse
from src.repository.crud.appointment import (
    create_appointment,
    fetch_appointment_by_id,
    fetch_doctor_appointments,
    mark_appointment_as_inactive_service,
)

from src.repository.crud.timeslot import (
    get_time_slot_by_id_from_db,
    update_time_slot_status,
)
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user

router = APIRouter()


@router.post(
    "/book_appointment",
    response_model=Appointment,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def book_appointment(
    appointment_data: AppointmentCreate, db: AsyncSession = Depends(get_db)
) -> Appointment:
    """
    Book an appointment with a doctor.

    Args:
        appointment_data (AppointmentCreate): The appointment data.
        db (AsyncSession): The database session.

    Returns:
        Appointment: The booked appointment.

    Raises:
        HTTPException: If the time slot is unavailable or if an error occurs.
    """
    try:
        time_slot = await get_time_slot_by_id_from_db(db, appointment_data.time_slot_id)
        if time_slot.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    detail="The selected time slot is unavailable",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ).dict(),
            )

        db_appointment = await create_appointment(db, appointment_data)
        await update_time_slot_status(db, appointment_data.time_slot_id, "booked")

        return Appointment.from_orm(db_appointment)
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Error booking the appointment",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/doctor/appointments",
    response_model=PagedAppointment,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def get_current_doctor_appointments(
    current_user: Doctor = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    params: Params = Depends(),
) -> PagedAppointment:
    """
    Retrieve paginated appointments for the currently logged-in doctor.

    Args:
        current_user (Doctor): The currently logged-in doctor (validated by role).
        db (AsyncSession): The database session.
        params (Params): Pagination parameters.

    Returns:
        PagedAppointment: Paginated list of appointments for the doctor.

    Raises:
        HTTPException: If no appointments are found for the doctor.
    """
    try:
        appointments = await fetch_doctor_appointments(db, current_user.user_id, params)

        if not appointments.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    detail="No appointments found for the specified doctor",
                    status_code=status.HTTP_404_NOT_FOUND,
                ).dict(),
            )

        return appointments
    except Exception as e:
        logger.error(f"Error retrieving doctor's appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Error retrieving the doctor's appointments",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.patch(
    "/appointments/{appointment_id}/inactive",
    responses={
        404: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def mark_appointment_as_inactive(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Doctor = Depends(get_current_user),
) -> dict:
    """
    Mark an appointment as inactive by the doctor.

    Args:
        appointment_id (UUID): The ID of the appointment to mark as inactive.
        db (AsyncSession): The database session.
        current_user (User): The current logged-in doctor.

    Returns:
        dict: A message indicating the result of the action.
    """
    try:
        appointment = await fetch_appointment_by_id(db, appointment_id)

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    detail=f"Appointment with ID {appointment_id} not found.",
                    status_code=status.HTTP_404_NOT_FOUND,
                ).dict(),
            )

        if appointment.doctor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    detail="You do not have permission to mark this appointment as inactive.",
                    status_code=status.HTTP_403_FORBIDDEN,
                ).dict(),
            )

        result = await mark_appointment_as_inactive_service(db, appointment_id)
        return {
            "message": "Appointment marked as inactive successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Unexpected error marking appointment inactive: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=f"Unexpected error occurred while marking appointment {appointment_id} inactive.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e
