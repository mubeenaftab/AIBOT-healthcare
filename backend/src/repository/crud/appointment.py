"""
Imports for handling appointment functionality in the FastAPI application.
Includes database models and schemas for appointment management.

- AsyncSession: Asynchronous database session management for SQLAlchemy.
- AppointmentModel: SQLAlchemy model representing the Appointment entity.
- AppointmentCreate: Pydantic schema for creating new appointments.
"""

from uuid import UUID


from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.appointment import Appointment as AppointmentModel
from src.models.schemas.appointment import AppointmentCreate, PagedAppointment


async def create_appointment(
    db: AsyncSession, appointment_data: AppointmentCreate
) -> AppointmentModel:
    """
    Create an appointment in the database.

    Args:
        db (AsyncSession): The database session.
        appointment_data (AppointmentCreate): The appointment data.

    Returns:
        AppointmentModel: The newly created appointment.
    """
    appointment = AppointmentModel(
        patient_id=appointment_data.patient_id,
        doctor_id=appointment_data.doctor_id,
        appointment_date=appointment_data.appointment_date,
        is_active=appointment_data.is_active,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment



async def fetch_doctor_appointments(
    db: AsyncSession, doctor_id: UUID, params: Params
) -> PagedAppointment:

    """
    Fetch paginated appointments for a specific doctor.

    Args:
        db (AsyncSession): The database session.
        doctor_id (UUID): The doctor's unique identifier.
        params (Params): Pagination parameters.

    Returns:
        PagedAppointment: A paginated result containing appointment objects.
    """
    try:
        query = select(AppointmentModel).where(AppointmentModel.doctor_id == doctor_id)
        query = query.order_by(AppointmentModel.appointment_date)
        result = await paginate(db, query, params)

        logger.info(
            f"Total appointments retrieved for doctor {doctor_id}: {len(result.items)}"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching doctor's appointments: {e}")
        raise



async def mark_appointment_as_inactive_service(
    db: AsyncSession, appointment_id: UUID
) -> dict:

    """
    Mark an appointment as inactive by setting its `is_active` field to False.

    Args:
        db (AsyncSession): The database session.
        appointment_id (UUID): The ID of the appointment to mark as inactive.

    Returns:
        dict: A message indicating success.
    """


    result = await db.execute(
        select(AppointmentModel).where(
            AppointmentModel.appointment_id == appointment_id
        )
    )

    appointment = result.scalars().first()

    if not appointment:
        raise ValueError(f"Appointment with ID {appointment_id} not found.")

    # Mark the appointment as inactive
    appointment.is_active = False
    await db.commit()
    await db.refresh(appointment)

    return {"appointment_id": str(appointment.appointment_id), "status": "inactive"}



async def fetch_appointment_by_id(
    db: AsyncSession, appointment_id: UUID
) -> AppointmentModel:

    """
    Fetch an appointment by its ID.

    Args:
        db (AsyncSession): The database session.
        appointment_id (UUID): The ID of the appointment to fetch.

    Returns:
        AppointmentModel: The fetched appointment, if found.
    """

    result = await db.execute(
        select(AppointmentModel).where(
            AppointmentModel.appointment_id == appointment_id
        )
    )
    appointment = result.scalars().first()
    return appointment
