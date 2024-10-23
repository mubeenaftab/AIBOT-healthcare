"""
Imports for handling user models, schemas, and asynchronous database operations.
Includes support for logging and password hashing.

- Optional: Provides type hinting for optional types.
- Pendulum: Date and time manipulation.
- AsyncSession: Asynchronous database session management.
- select: SQL SELECT statement construction.
- logger: Application logging configuration.
- PatientModel: Database models for user entities.
- PatientCreate: Pydantic schemas for user creation.
- get_password_hash, verify_password: Functions for secure password handling.
"""

from typing import Optional
from uuid import UUID

import pendulum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.user import Patient as PatientModel

from src.models.schemas.patient import PatientCreate, PatientUpdate
from src.securities.hashing.hash import get_password_hash, verify_password


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
            email=patient.email,
            city=patient.city,
            phone_number=patient.phone_number,
            dob=patient.dob,
            gender=patient.gender,
            blood_group=patient.blood_group,
            emergency_contact=patient.emergency_contact,
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
        patient_id (UUID): The ID of the patient to update.
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
        if patient_update.email:
            db_patient.email = patient_update.email
        if patient_update.city:
            db_patient.city = patient_update.city
        if patient_update.dob:
            db_patient.dob = patient_update.dob
        if patient_update.gender:
            db_patient.gender = patient_update.gender
        if patient_update.blood_group:
            db_patient.blood_group = patient_update.blood_group
        if patient_update.emergency_contact:
            db_patient.emergency_contact = patient_update.emergency_contact

        # Commit the changes
        await db.commit()
        await db.refresh(db_patient)
        logger.info(f"Patient with ID {patient_id} updated successfully")
        return db_patient
    except ValueError as e:
        logger.error(f"Patient update error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating patient with ID {patient_id}: {e}")
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
