from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.db.user import Doctor as DoctorModel
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.doctor import Doctor, DoctorCreate, DoctorUpdate
from src.repository.crud.doctor import (
    create_doctor,
    get_doctor_by_id_from_db,
    get_doctors_by_specialization_from_db,
    update_doctor,
)
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user
from src.utilities.constants import ErrorMessages

router = APIRouter()


@router.post(
    "/register/doctor",
    response_model=Doctor,
    responses={500: {"model": ErrorResponse}},
)
async def register_doctor(
    doctor: DoctorCreate, db: AsyncSession = Depends(get_db)
) -> Doctor:
    """
    Register a new doctor.

    Args:
        doctor (DoctorCreate): The doctor data for registration.
        db (Session): The database session.

    Returns:
        DoctorSchema: The registered doctor.

    Raises:
        HTTPException: If there's an error during doctor creation.
    """
    try:
        logger.info(f"Attempting to register doctor with username: {doctor.username}")
        db_doctor = await create_doctor(db, doctor)
        logger.info(f"Doctor registered successfully with ID: {db_doctor.user_id}")
        return Doctor.from_orm(db_doctor)
    except Exception as e:
        logger.error(f"Unexpected error during doctor registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=ErrorMessages.DOCTOR_EXISTS.value,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.put(
    "/update/doctor/{doctor_id}",
    response_model=Doctor,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def update_doctor_endpoint(
    doctor_id: UUID,
    doctor_update: DoctorUpdate,
    current_user: DoctorModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """
    Update an existing doctor's details.

    Args:
        doctor_id (UUID): The ID of the doctor to update.
        doctor_update (DoctorUpdate): The doctor data to update.
        db (AsyncSession): The database session.

    Returns:
        Doctor: The updated doctor data.

    Raises:
        HTTPException: If doctor is not found or an error occurs during update.
    """
    try:
        logger.info(f"Attempting to update doctor with ID: {doctor_id}")
        updated_doctor = await update_doctor(db, current_user.user_id, doctor_update)
        logger.info(f"Doctor updated successfully with ID: {updated_doctor.user_id}")
        return Doctor.from_orm(updated_doctor)
    except ValueError as e:
        logger.error(f"Doctor with ID {current_user.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=ErrorMessages.NO_DOCTOR_FOUND.value,
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during doctor update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=ErrorMessages.DOCTOR_UPDATE_ERROR.value,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/doctors",
    response_model=list[Doctor],
    responses={404: {"model": ErrorResponse}},
)
async def get_doctors_by_specialization(
    specialization: str, db: AsyncSession = Depends(get_db)
) -> list[Doctor]:
    """
    Get a list of doctors based on specialization.

    Args:
        specialization (str): The specialization of the doctor.
        db (AsyncSession): The database session.

    Returns:
        List[Doctor]: A list of doctors with the specified specialization.

    Raises:
        HTTPException: If no doctors are found.
    """
    logger.debug(f"Searching for doctors with specialization: '{specialization}'")
    doctors = await get_doctors_by_specialization_from_db(db, specialization)
    if not doctors:
        logger.warning(f"No doctors found for specialization: '{specialization}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=ErrorMessages.NO_DOCTORS_FOUND_FOR_SPECIALIZATION.value.format(
                    specialization
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )
    return [Doctor.from_orm(doctor) for doctor in doctors]


@router.get(
    "/doctors/{doctor_id}",
    response_model=Doctor,
    responses={404: {"model": ErrorResponse}},
)
async def get_doctor_by_id(
    doctor_id: str, db: AsyncSession = Depends(get_db)
) -> Doctor:
    """
    Get a doctor by ID.

    Args:
        doctor_id (str): The ID of the doctor.
        db (AsyncSession): The database session.

    Returns:
        Doctor: The doctor with the specified ID.

    Raises:
        HTTPException: If the doctor is not found.
    """
    logger.info(f"Fetching doctor with ID: {doctor_id}")

    doctor = await get_doctor_by_id_from_db(db, doctor_id)

    if not doctor:
        logger.warning(f"Doctor with ID {doctor_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=ErrorMessages.NO_DOCTOR_FOUND.value.format(doctor_id),
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )

    logger.info(f"Doctor with ID {doctor_id} found: {doctor}")
    return Doctor.from_orm(doctor)
