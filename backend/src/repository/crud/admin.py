from typing import List, Optional
from uuid import UUID

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.settings.logger_config import logger
from src.models.db.appointment import Appointment as AppointmentModel
from src.models.db.user import Doctor as DoctorModel, Patient as PatientModel
from src.models.schemas.appointment import PagedAppointment
from src.models.schemas.user import PagedDoctor, PagedPatient


async def get_all_appointments(
    db: AsyncSession,
    params: Params,
) -> PagedAppointment:
    """
    Retrieve a paginated list of all appointments from the database, ordered by appointment date in descending order.

    Args:
        db (AsyncSession): The database session.
        params (Params): Pagination parameters.

    Returns:
        PagedAppointment: A paginated result containing appointment objects.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    try:
        query = select(AppointmentModel)
        query = query.order_by(desc(AppointmentModel.appointment_date))
        result = await paginate(db, query, params)
        logger.info(f"Total appointments retrieved: {len(result.items)}")
        return result
    except Exception as e:
        logger.error(f"Error retrieving all appointments: {e}")
        raise


async def get_all_doctors(
    db: AsyncSession,
    params: Params,
    search: Optional[str] = None,
) -> PagedDoctor:
    """
    Retrieve a paginated list of all doctors from the database. Allows optional search by username, first name, last name, or specialization.

    Args:
        db (AsyncSession): The database session.
        params (Params): Pagination parameters.
        search (Optional[str]): A search query to filter doctors based on username, first name, last name, or specialization.

    Returns:
        PagedDoctor: A paginated result containing doctor objects.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    try:
        query = select(DoctorModel)
        if search:
            search = search.lower()
            query = query.filter(
                func.lower(DoctorModel.username).ilike(f"%{search}%")
                | func.lower(DoctorModel.first_name).ilike(f"%{search}%")
                | func.lower(DoctorModel.last_name).ilike(f"%{search}%")
                | func.lower(DoctorModel.specialization).ilike(f"%{search}%")
            )
        result = await paginate(db, query, params)
        logger.info(f"Total doctors retrieved: {len(result.items)}")
        return result
    except Exception as e:
        logger.error(f"Error retrieving all doctors: {e}")
        raise


async def get_all_patients(
    db: AsyncSession,
    params: Params,
    search: Optional[str] = None,
) -> PagedPatient:
    """
    Retrieve a paginated list of all patients from the database. Allows optional search by username, first name, or last name.

    Args:
        db (AsyncSession): The database session.
        params (Params): Pagination parameters.
        search (Optional[str]): A search query to filter patients based on username, first name, or last name.

    Returns:
        PagedPatient: A paginated result containing patient objects.

    Raises:
        Exception: If an error occurs during the retrieval process.
    """
    try:
        query = select(PatientModel)
        if search:
            search = search.lower()
            query = query.filter(
                func.lower(PatientModel.username).ilike(f"%{search}%")
                | func.lower(PatientModel.first_name).ilike(f"%{search}%")
                | func.lower(PatientModel.last_name).ilike(f"%{search}%")
            )
        result = await paginate(db, query, params)
        logger.info(f"Total patients retrieved: {len(result.items)}")
        return result
    except Exception as e:
        logger.error(f"Error retrieving all patients: {e}")
        raise


async def delete_doctor(
    db: AsyncSession,
    doctor_id: UUID,
) -> bool:
    """
    Delete a doctor from the database.

    Args:
        db (AsyncSession): The database session.
        doctor_id (UUID): The ID of the doctor to delete.

    Returns:
        bool: True if the doctor was deleted, False if the doctor was not found.

    Raises:
        Exception: If there is an error during the deletion.
    """
    try:
        result = await db.execute(delete(DoctorModel).where(DoctorModel.user_id == doctor_id))
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting doctor: {e}")
        raise


async def delete_patient(
    db: AsyncSession,
    patient_id: UUID,
) -> bool:
    """
    Delete a patient from the database.

    Args:
        db (AsyncSession): The database session.
        patient_id (UUID): The ID of the patient to delete.

    Returns:
        bool: True if the patient was deleted, False if the patient was not found.

    Raises:
        Exception: If there is an error during the deletion.
    """
    try:
        result = await db.execute(delete(PatientModel).where(PatientModel.user_id == patient_id))
        await db.commit()
        return result.rowcount > 0
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting patient: {e}")
        raise
