"""
Imports for handling appointment functionality in the FastAPI application.
Includes database models and schemas for appointment management.

- AsyncSession: Asynchronous database session management for SQLAlchemy.
- AppointmentModel: SQLAlchemy model representing the Appointment entity.
- AppointmentCreate: Pydantic schema for creating new appointments.
"""

from typing import Optional
from uuid import UUID

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.appointment import Appointment as AppointmentModel
from src.models.db.user import Patient
from src.models.schemas.appointment import AppointmentCreate, PagedAppointment
from src.repository.crud.timeslot import delete_oldest_timeslot_by_doctor_and_patient


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


async def fetch_doctor_active_appointments(
    db: AsyncSession,
    doctor_id: UUID,
    params: Params,
    search: Optional[str] = None,
    sort_order: str = "desc",
) -> PagedAppointment:
    """
    Fetch paginated active appointments for a specific doctor with optional search and sorting.

    Args:
        db (AsyncSession): The database session.
        doctor_id (UUID): The doctor's unique identifier.
        params (Params): Pagination parameters.
        search (Optional[str]): Search keyword for filtering by patient name.
        sort_order (str): Sort order for appointment date, either 'asc' or 'desc'.

    Returns:
        PagedAppointment: A paginated result containing appointment objects.
    """
    try:
        # Modify the query to filter by active appointments
        query = (
            select(AppointmentModel)
            .join(Patient, AppointmentModel.patient_id == Patient.user_id)
            .where(
                AppointmentModel.doctor_id == doctor_id,
                AppointmentModel.is_active == True,  # Filter by active appointments
            )
        )

        if search:
            search = search.lower()
            query = query.filter(
                (func.lower(Patient.first_name).ilike(f"%{search}%"))
                | (func.lower(Patient.last_name).ilike(f"%{search}%"))
            )

        if sort_order == "asc":
            query = query.order_by(asc(AppointmentModel.appointment_date))
        else:
            query = query.order_by(desc(AppointmentModel.appointment_date))

        # Execute the paginated query
        result = await paginate(db, query, params)

        logger.info(
            f"Total active appointments retrieved for doctor {doctor_id}: {len(result.items)}"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching doctor's appointments: {e}")
        raise


async def fetch_doctor_inactive_appointments(
    db: AsyncSession,
    doctor_id: UUID,
    params: Params,
    search: Optional[str] = None,
    sort_order: str = "desc",
) -> PagedAppointment:
    """
    Fetch paginated active appointments for a specific doctor with optional search and sorting.

    Args:
        db (AsyncSession): The database session.
        doctor_id (UUID): The doctor's unique identifier.
        params (Params): Pagination parameters.
        search (Optional[str]): Search keyword for filtering by patient name.
        sort_order (str): Sort order for appointment date, either 'asc' or 'desc'.

    Returns:
        PagedAppointment: A paginated result containing appointment objects.
    """
    try:
        # Modify the query to filter by active appointments
        query = (
            select(AppointmentModel)
            .join(Patient, AppointmentModel.patient_id == Patient.user_id)
            .where(
                AppointmentModel.doctor_id == doctor_id,
                AppointmentModel.is_active == False,  # Filter by active appointments
            )
        )

        if search:
            search = search.lower()
            query = query.filter(
                (func.lower(Patient.first_name).ilike(f"%{search}%"))
                | (func.lower(Patient.last_name).ilike(f"%{search}%"))
            )

        if sort_order == "asc":
            query = query.order_by(asc(AppointmentModel.appointment_date))
        else:
            query = query.order_by(desc(AppointmentModel.appointment_date))

        # Execute the paginated query
        result = await paginate(db, query, params)

        logger.info(
            f"Total active appointments retrieved for doctor {doctor_id}: {len(result.items)}"
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
    After marking the appointment as inactive, delete the oldest associated time slot
    where the patient and doctor IDs match.

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

    appointment.is_active = False
    await db.commit()
    await db.refresh(appointment)

    await delete_oldest_timeslot_by_doctor_and_patient(db, appointment)

    return {"appointment_id": str(appointment.appointment_id), "status": "inactive"}


async def get_inactive_appointment(
    db: AsyncSession, patient_id: int
) -> AppointmentModel | None:
    """
    Retrieve the most recent inactive appointment for the specified patient.

    Args:
        db (AsyncSession): The database session to execute queries.
        patient_id (int): The ID of the patient.

    Returns:
        AppointmentModel | None: The inactive appointment if found, otherwise None.
    """
    inactive_appointments = await db.execute(
        select(AppointmentModel)
        .where(AppointmentModel.patient_id == patient_id)
        .where(AppointmentModel.is_active.is_(False))
        .order_by(AppointmentModel.appointment_date.desc())
    )
    inactive_appointment = inactive_appointments.scalars().first()
    logger.debug(f"inactive_appointment: {inactive_appointment}")
    return inactive_appointment


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
