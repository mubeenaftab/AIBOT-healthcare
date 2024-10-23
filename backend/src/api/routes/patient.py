from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.db.user import Patient as PatientModel
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.patient import Patient, PatientCreate, PatientUpdate
from src.repository.crud.patient import (
    create_patient,
    get_patient_by_id_from_db,
    update_patient,
)
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user
from src.utilities.constants import ErrorMessages

router = APIRouter()


@router.post(
    "/register/patient",
    response_model=Patient,
    responses={500: {"model": ErrorResponse}},
)
async def register_patient(
    patient: PatientCreate, db: AsyncSession = Depends(get_db)
) -> Patient:
    """
    Register a new patient.

    Args:
        patient (PatientCreate): The patient data for registration.
        db (Session): The database session.

    Returns:
        PatientSchema: The registered patient.

    Raises:
        HTTPException: If there's an error during patient creation.
    """
    try:
        logger.info(f"Attempting to register patient with username: {patient.username}")
        db_patient = await create_patient(db, patient)
        logger.info(f"Patient registered successfully with ID: {db_patient.user_id}")
        return Patient.from_orm(db_patient)
    except Exception as e:
        logger.error(f"Unexpected error during patient registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=ErrorMessages.PATIENT_EXISTS.value,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.put(
    "/update/patient/{patient_id}",
    response_model=Patient,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def update_patient_endpoint(
    patient_id: UUID,
    patient_update: PatientUpdate,
    current_user: PatientModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """
    Update an existing patient's details.

    Args:
        patient_id (int): The ID of the patient to update.
        patient_update (PatientUpdate): The patient data to update.
        db (AsyncSession): The database session.

    Returns:
        Patient: The updated patient data.

    Raises:
        HTTPException: If patient is not found or an error occurs during update.
    """
    try:
        logger.info(f"Attempting to update patient with ID: {patient_id}")
        updated_patient = await update_patient(db, current_user.user_id, patient_update)
        logger.info(f"Patient updated successfully with ID: {updated_patient.user_id}")
        return Patient.from_orm(updated_patient)
    except ValueError as e:
        logger.error(f"Patient with ID {current_user.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=ErrorMessages.PATIENT_NOT_FOUND.value,
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during patient update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=ErrorMessages.PATIENT_UPDATE_ERROR.value,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/patients/{patient_id}",
    response_model=Patient,
    responses={404: {"model": ErrorResponse}},
)
async def get_patient_by_id(
    patient_id: str, db: AsyncSession = Depends(get_db)
) -> Patient:
    """
    Get a patient by ID.

    Args:
        patient_id (str): The ID of the patient.
        db (AsyncSession): The database session.

    Returns:
        Patient: The patient with the specified ID.

    Raises:
        HTTPException: If the patient is not found.
    """
    logger.info(f"Fetching patient with ID: {patient_id}")

    patient = await get_patient_by_id_from_db(db, patient_id)

    if not patient:
        logger.warning(f"Patient with ID {patient_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=ErrorMessages.NO_PATIENT_FOUND.value.format(patient_id),
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )

    logger.info(f"Patient with ID {patient_id} found: {patient}")
    return Patient.from_orm(patient)
