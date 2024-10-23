"""
Imports for handling user models, schemas, and asynchronous database operations.
Includes support for logging and password hashing.

- Optional: Provides type hinting for optional types.
- Pendulum: Date and time manipulation.
- AsyncSession: Asynchronous database session management.
- select: SQL SELECT statement construction.
- logger: Application logging configuration.
- DoctorModel: Database models for user entities.
- DoctorCreate: Pydantic schemas for user creation.
- get_password_hash, verify_password: Functions for secure password handling.
"""

from typing import Optional
from uuid import UUID

import pendulum
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.user import Doctor as DoctorModel
from src.models.schemas.doctor import DoctorCreate, DoctorUpdate
from src.securities.hashing.hash import get_password_hash, verify_password
from src.utilities.specialization_mapper import SpecializationMapper


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
            email=doctor.email,
            city=doctor.city,
            specialization=doctor.specialization,
            phone_number=doctor.phone_number,
            gender=doctor.gender,
            years_of_experience=doctor.years_of_experience,
            consultation_fee=doctor.consultation_fee,
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
        if doctor_update.email:
            db_doctor.email = doctor_update.email
        if doctor_update.city:
            db_doctor.city = doctor_update.city
        if doctor_update.specialization:
            db_doctor.specialization = doctor_update.specialization
        if doctor_update.gender:
            db_doctor.gender = doctor_update.gender
        if doctor_update.years_of_experience is not None:
            db_doctor.years_of_experience = doctor_update.years_of_experience
        if doctor_update.consultation_fee is not None:
            db_doctor.consultation_fee = doctor_update.consultation_fee

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
        mapper = SpecializationMapper()
        
        matching_specializations = mapper.find_matching_specializations(specialization)
        
        logger.info(f"Searching for doctors with specializations matching: {matching_specializations}")
        
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
