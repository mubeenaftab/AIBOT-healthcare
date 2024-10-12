from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import add_pagination, Params
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings.logger_config import logger
from src.models.schemas.appointment import PagedAppointment
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.user import PagedDoctor, PagedPatient
from src.repository.crud.admin import (
    delete_doctor,
    delete_patient,
    get_all_appointments,
    get_all_doctors,
    get_all_patients,
)
from src.repository.database import get_db

router = APIRouter()


@router.get(
    "/admin/appointments",
    response_model=PagedAppointment,
    responses={
        500: {"model": ErrorResponse},
    },
)
async def get_all_appointments_endpoint(
    db: AsyncSession = Depends(get_db),
    params: Params = Depends(),
) -> PagedAppointment:
    """
    Retrieve all appointments with pagination.

    This endpoint allows retrieval of all appointments in the system, paginated based on query parameters.

    Args:
        db (AsyncSession): The database session dependency.
        params (Params): Pagination parameters.

    Returns:
        PagedAppointment: A paginated list of appointments.

    Raises:
        HTTPException: If an internal server error occurs during the retrieval process.
    """
    try:
        logger.info("Fetching appointments with pagination")
        appointments = await get_all_appointments(db, params=params)
        return appointments
    except Exception as e:
        logger.error(f"Unexpected error while retrieving appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving appointments.",
        ) from e


@router.get(
    "/admin/doctors",
    response_model=PagedDoctor,
    responses={
        500: {"model": ErrorResponse},
    },
)
async def get_all_doctors_endpoint(
    db: AsyncSession = Depends(get_db),
    params: Params = Depends(),
    search: Optional[str] = None,
) -> PagedDoctor:
    """
    Retrieve all doctors with optional search and pagination.

    This endpoint allows retrieval of all doctors in the system, with optional search functionality to filter by username, first name, last name, or specialization, and paginated based on query parameters.

    Args:
        db (AsyncSession): The database session dependency.
        params (Params): Pagination parameters.
        search (Optional[str]): Optional search query to filter doctors.

    Returns:
        PagedDoctor: A paginated list of doctors.

    Raises:
        HTTPException: If an internal server error occurs during the retrieval process.
    """
    try:
        logger.info("Fetching doctors with pagination")
        paginated_doctors = await get_all_doctors(db, params=params, search=search)
        return paginated_doctors
    except Exception as e:
        logger.error(f"Unexpected error while retrieving doctors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving doctors.",
        ) from e


@router.get(
    "/admin/patients",
    response_model=PagedPatient,
    responses={
        500: {"model": ErrorResponse},
    },
)
async def get_all_patients_endpoint(
    db: AsyncSession = Depends(get_db),
    params: Params = Depends(),
    search: Optional[str] = None,
) -> PagedPatient:
    """
    Retrieve all patients with optional search and pagination.

    This endpoint allows retrieval of all patients in the system, with optional search functionality to filter by username, first name, or last name, and paginated based on query parameters.

    Args:
        db (AsyncSession): The database session dependency.
        params (Params): Pagination parameters.
        search (Optional[str]): Optional search query to filter patients.

    Returns:
        PagedPatient: A paginated list of patients.

    Raises:
        HTTPException: If an internal server error occurs during the retrieval process.
    """
    try:
        logger.info("Fetching patients with pagination")
        patients = await get_all_patients(db, search=search, params=params)
        return patients
    except Exception as e:
        logger.error(f"Unexpected error while retrieving patients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving patients.",
        ) from e


@router.delete(
    "/admin/doctors/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def delete_doctor_endpoint(
    doctor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a doctor by their ID.

    This endpoint allows an admin to delete a specific doctor using their unique identifier.

    Args:
        doctor_id: The UUID of the doctor to delete.
        db: The database session for performing the operation.

    Raises:
        HTTPException: If the doctor is not found or if there's an unexpected error.
    """
    try:
        deleted = await delete_doctor(db, doctor_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID: {doctor_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting doctor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting the doctor.",
        ) from e


@router.delete(
    "/admin/patients/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def delete_patient_endpoint(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a patient by their ID.

    This endpoint allows an admin to delete a specific patient using their unique identifier.

    Args:
        patient_id: The UUID of the patient to delete.
        db: The database session for performing the operation.

    Raises:
        HTTPException: If the patient is not found or if there's an unexpected error.
    """
    try:
        deleted = await delete_patient(db, patient_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID: {patient_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting patient: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting the patient.",
        ) from e


add_pagination(router)
