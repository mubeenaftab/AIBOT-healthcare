"""
Imports for handling user models, schemas, and asynchronous database operations.
Includes support for logging and password hashing.

- Optional: Provides type hinting for optional types.
- Pendulum: Date and time manipulation.
- AsyncSession: Asynchronous database session management.
- select: SQL SELECT statement construction.
- logger: Application logging configuration.
- AdminModel, DoctorModel, PatientModel: Database models for user entities.
- AdminCreate, DoctorCreate, PatientCreate: Pydantic schemas for user creation.
- get_password_hash, verify_password: Functions for secure password handling.
"""

from typing import Optional
from uuid import UUID

import pendulum
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.user import Admin as AdminModel
from src.models.db.user import Doctor as DoctorModel
from src.models.db.user import Patient as PatientModel
from src.models.schemas.user import (
    AdminCreate,
    DoctorCreate,
    DoctorUpdate,
    PatientCreate,
    PatientUpdate,
)
from src.securities.hashing.hash import get_password_hash, verify_password
from src.utilities.specialization_mapper import SpecializationMapper


async def create_patient(db: AsyncSession, patient: PatientCreate) -> PatientModel:
    """
    Creates a new patient record in the database.

    Args:
        db (AsyncSession): The database session for async operations.
        patient (PatientCreate): The patient data for creation.

    Returns:
        PatientModel: The created patient model instance.

    Raises:
        Exception: Raises an exception if there is an error during the patient creation process.
    """
    try:
        hashed_password = await get_password_hash(patient.password)
        db_patient = PatientModel(
            username=patient.username,
            hashed_password=hashed_password,
            first_name=patient.first_name,
            last_name=patient.last_name,
            phone_number=patient.phone_number,
            dob=patient.dob,
            timestamp=pendulum.now().naive(),
        )
        db.add(db_patient)
        await db.commit()
        await db.refresh(db_patient)
        logger.info(f"Patient created successfully with username: {patient.username}")
        return db_patient
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise


async def update_patient(
    db: AsyncSession, patient_id: UUID, patient_update: PatientUpdate
) -> PatientModel:
    """
    Updates an existing patient record in the database.

    Args:
        db (AsyncSession): The database session for async operations.
        patient_id (int): The ID of the patient to update.
        patient_update (PatientUpdate): The patient data to update.

    Returns:
        PatientModel: The updated patient model instance.

    Raises:
        PatientNotFoundError: If the patient is not found in the database.
        Exception: If there is any other error during the update process.
    """
    try:
        db_patient = await db.get(PatientModel, patient_id)
        if not db_patient:
            logger.warning(f"Patient with ID {patient_id} not found")
            raise ValueError("Patient not found")

        if patient_update.password:
            db_patient.hashed_password = await get_password_hash(
                patient_update.password
            )
        if patient_update.first_name:
            db_patient.first_name = patient_update.first_name
        if patient_update.last_name:
            db_patient.last_name = patient_update.last_name
        if patient_update.phone_number:
            db_patient.phone_number = patient_update.phone_number
        if patient_update.dob:
            db_patient.dob = patient_update.dob

        # Commit the changes
        await db.commit()
        await db.refresh(db_patient)
        logger.info(f"Patient with ID {patient_id} updated successfully")
        return db_patient
    except ValueError as e:
        logger.error(f" Pateint update error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating patient with ID {patient_id}: {e}")
        raise


async def create_doctor(db: AsyncSession, doctor: DoctorCreate) -> DoctorModel:
    """
    Creates a new doctor record in the database.

    Args:
        db (AsyncSession): The database session for async operations.
        doctor (DoctorCreate): The doctor data for creation.

    Returns:
        DoctorModel: The created doctor model instance.

    Raises:
        Exception: Raises an exception if there is an error during the doctor creation process.
    """
    try:
        hashed_password = await get_password_hash(doctor.password)
        db_doctor = DoctorModel(
            username=doctor.username,
            hashed_password=hashed_password,
            first_name=doctor.first_name,
            last_name=doctor.last_name,
            specialization=doctor.specialization,
            phone_number=doctor.phone_number,
            timestamp=pendulum.now().naive(),
        )
        db.add(db_doctor)
        await db.commit()
        await db.refresh(db_doctor)
        logger.info(f"Doctor created successfully with username: {doctor.username}")
        return db_doctor
    except Exception as e:
        logger.error(f"Error creating doctor: {e}")
        raise


async def update_doctor(
    db: AsyncSession, doctor_id: UUID, doctor_update: DoctorUpdate
) -> DoctorModel:
    """
    Updates an existing doctor record in the database.

    Args:
        db (AsyncSession): The database session for async operations.
        doctor_id (UUID): The ID of the doctor to update.
        doctor_update (DoctorUpdate): The doctor data to update.

    Returns:
        DoctorModel: The updated doctor model instance.

    Raises:
        DoctorNotFoundError: If the doctor is not found in the database.
        Exception: If there is any other error during the update process.
    """
    try:
        db_doctor = await db.get(DoctorModel, doctor_id)
        if not db_doctor:
            logger.warning(f"Doctor with ID {doctor_id} not found")
            raise ValueError("Doctor not found")

        if doctor_update.password:
            db_doctor.hashed_password = await get_password_hash(doctor_update.password)
        if doctor_update.first_name:
            db_doctor.first_name = doctor_update.first_name
        if doctor_update.last_name:
            db_doctor.last_name = doctor_update.last_name
        if doctor_update.phone_number:
            db_doctor.phone_number = doctor_update.phone_number
        if doctor_update.specialization:
            db_doctor.specialization = doctor_update.specialization

        # Commit the changes
        await db.commit()
        await db.refresh(db_doctor)
        logger.info(f"Doctor with ID {doctor_id} updated successfully")
        return db_doctor
    except ValueError as e:
        logger.error(f"Doctor update error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating doctor with ID {doctor_id}: {e}")
        raise


async def create_admin(db: AsyncSession, admin: AdminCreate) -> AdminModel:
    """
    Creates a new admin record in the database.

    Args:
        db (AsyncSession): The database session for async operations.
        admin (AdminCreate): The admin data for creation.

    Returns:
        AdminModel: The created admin model instance.

    Raises:
        Exception: Raises an exception if there is an error during the admin creation process.
    """
    try:
        hashed_password = await get_password_hash(admin.password)
        db_admin = AdminModel(
            username=admin.username,
            hashed_password=hashed_password,
            timestamp=pendulum.now().naive(),
        )
        db.add(db_admin)
        await db.commit()
        await db.refresh(db_admin)
        logger.info(f"Admin created successfully with username: {admin.username}")
        return db_admin
    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        raise


async def authenticate_patient(
    db: AsyncSession, username: str, password: str
) -> Optional[PatientModel]:
    """
    Authenticates a patient by verifying the username and password.

    Args:
        db (AsyncSession): The database session for async operations.
        username (str): The patient's username.
        password (str): The patient's password.

    Returns:
        Optional[PatientModel]: The authenticated patient object, or None if authentication fails.

    Raises:
        Exception: Raises an exception if there is an error during the authentication process.
    """
    try:
        stmt = select(PatientModel).filter(PatientModel.username == username)
        result = await db.execute(stmt)
        patient = result.scalar_one_or_none()

        if patient is None or not await verify_password(
            password, patient.hashed_password
        ):
            logger.warning(
                f"Authentication failed for patient with username: {username}"
            )
            return None

        logger.info(f"Patient authenticated successfully with username: {username}")
        return patient

    except Exception as e:
        logger.error(f"Error during patient authentication: {e}")
        raise


async def authenticate_doctor(
    db: AsyncSession, username: str, password: str
) -> Optional[DoctorModel]:
    """
    Authenticates a doctor by verifying the username and password.

    Args:
        db (AsyncSession): The database session for async operations.
        username (str): The doctor's username.
        password (str): The doctor's password.

    Returns:
        Optional[DoctorModel]: The authenticated doctor object, or None if authentication fails.

    Raises:
        Exception: Raises an exception if there is an error during the authentication process.
    """
    try:
        stmt = select(DoctorModel).filter(DoctorModel.username == username)
        result = await db.execute(stmt)
        doctor = result.scalar_one_or_none()

        if doctor is None or not await verify_password(
            password, doctor.hashed_password
        ):
            logger.warning(
                f"Authentication failed for doctor with username: {username}"
            )
            return None

        logger.info(f"Doctor authenticated successfully with username: {username}")
        return doctor

    except Exception as e:
        logger.error(f"Error during doctor authentication: {e}")
        raise


async def authenticate_admin(
    db: AsyncSession, username: str, password: str
) -> Optional[AdminModel]:
    """
    Authenticates an admin by verifying the username and password.

    Args:
        db (AsyncSession): The database session for async operations.
        username (str): The admin's username.
        password (str): The admin's password.

    Returns:
        Optional[AdminModel]: The authenticated admin object, or None if authentication fails.

    Raises:
        Exception: Raises an exception if there is an error during the authentication process.
    """
    try:
        stmt = select(AdminModel).filter(AdminModel.username == username)
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin is None or not await verify_password(password, admin.hashed_password):
            logger.warning(f"Authentication failed for admin with username: {username}")
            return None

        logger.info(f"Admin authenticated successfully with username: {username}")
        return admin

    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        raise


async def get_doctors_by_specialization_from_db(
    db: AsyncSession,
    specialization: str
) -> list[DoctorModel]:
    """
    Fetch doctors by specialization from the database using flexible matching.

    Args:
        db (AsyncSession): The database session.
        specialization (str): The specialization to filter doctors by.

    Returns:
        List[DoctorModel]: List of doctors with matching specializations.
    """
    try:
        # Initialize the specialization mapper
        mapper = SpecializationMapper()
        
        # Get all possible matching specializations
        matching_specializations = mapper.find_matching_specializations(specialization)
        
        logger.info(f"Searching for doctors with specializations matching: {matching_specializations}")
        
        # Create a query that matches any of the possible specializations
        query = select(DoctorModel).where(
            or_(*[
                func.lower(func.trim(DoctorModel.specialization)).like(f"%{spec.lower().strip()}%")
                for spec in matching_specializations
            ])
        )
        
        result = await db.execute(query)
        doctors = result.scalars().all()
        
        logger.info(f"Found {len(doctors)} matching doctors for specialization '{specialization}'")
        return doctors
        
    except Exception as e:
        logger.error(f"Error fetching doctors by specialization: {e}")
        raise



async def get_doctor_by_id_from_db(db: AsyncSession, doctor_id: str) -> DoctorModel:
    """
    Fetch a doctor by ID from the database.

    Args:
        db (AsyncSession): The database session.
        doctor_id (str): The ID of the doctor.

    Returns:
        DoctorModel: The doctor with the specified ID, or None if not found.
    """
    logger.info(f"Fetching doctor with ID: {doctor_id}")
    result = await db.execute(
        select(DoctorModel).where(DoctorModel.user_id == doctor_id)
    )
    doctor = result.scalar()

    if doctor:
        logger.info(f"Doctor found: {doctor}")
    else:
        logger.warning(f"No doctor found with ID: {doctor_id}")

    return doctor


async def get_patient_by_id_from_db(db: AsyncSession, patient_id: str) -> PatientModel:
    """
    Fetch a patient by ID from the database.

    Args:
        db (AsyncSession): The database session.
        patient_id (str): The ID of the patient.

    Returns:
        PatientModel: The patient with the specified ID, or None if not found.
    """
    logger.info(f"Fetching patient with ID: {patient_id}")
    result = await db.execute(
        select(PatientModel).where(PatientModel.user_id == patient_id)
    )
    patient = result.scalar()

    if patient:
        logger.info(f"Patient found: {patient}")
    else:
        logger.warning(f"No patient found with ID: {patient_id}")

    return patient
