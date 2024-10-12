from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings.logger_config import logger
from src.models.db.user import Doctor
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.prescription import Prescription, PrescriptionCreate, PrescriptionUpdate
from src.repository.crud.prescription import (
    create_prescription,
    delete_prescription,
    get_prescription,
    update_prescription,
)
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user

router = APIRouter()


@router.post(
    "/prescriptions",
    response_model=Prescription,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_prescription_endpoint(
    prescription_data: PrescriptionCreate,
    current_user: Doctor = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Prescription:
    """
    Create a new prescription for a patient by the currently logged-in doctor.

    Args:
        prescription_data (PrescriptionCreate): The data for the new prescription.
        current_user (Doctor): The authenticated doctor creating the prescription.
        db (AsyncSession): The database session.

    Returns:
        Prescription: The created prescription object.

    Raises:
        HTTPException: If there's an unexpected error during prescription creation.
    """
    try:
        logger.info(f"Doctor {current_user.user_id} is creating a prescription.")
        prescription = await create_prescription(db, prescription_data, current_user.user_id)
        logger.info(f"Prescription created successfully with ID: {prescription.prescription_id}")
        return Prescription.from_orm(prescription)
    except Exception as e:
        logger.error(f"Unexpected error during prescription creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Internal server error occurred while creating the prescription.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=Prescription,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_prescription_endpoint(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Prescription:
    """
    Retrieve a prescription by its ID.

    This endpoint allows retrieval of a specific prescription using its unique identifier.

    Args:
        prescription_id: The UUID of the prescription to retrieve.
        db: The database session for performing the operation.

    Returns:
        The requested Prescription object.

    Raises:
        HTTPException: If the prescription is not found or if there's an unexpected error.
    """
    try:
        prescription = await get_prescription(db, prescription_id)
        if not prescription:
            logger.warning(f"Prescription with ID: {prescription_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID: {prescription_id} not found",
            )
        return Prescription.from_orm(prescription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prescription update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating the prescription.",
        ) from e


@router.put(
    "/prescriptions/{prescription_id}",
    response_model=Prescription,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def update_prescription_endpoint(
    prescription_id: UUID,
    prescription_data: PrescriptionUpdate,
    db: AsyncSession = Depends(get_db),
) -> Prescription:
    """
    Update a prescription by its ID.

    This endpoint allows updating the details of an existing prescription.

    Args:
        prescription_id: The UUID of the prescription to update.
        prescription_data: The updated data for the prescription.
        db: The database session for performing the operation.

    Returns:
        The updated Prescription object.

    Raises:
        HTTPException: If the prescription is not found or if there's an unexpected error.
    """
    try:
        updated_prescription = await update_prescription(db, prescription_id, prescription_data)
        if not updated_prescription:
            logger.warning(f"Prescription with ID: {prescription_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID: {prescription_id} not found",
            )
        return Prescription.from_orm(updated_prescription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prescription update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating the prescription.",
        ) from e


@router.delete(
    "/prescriptions/{prescription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def delete_prescription_endpoint(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a prescription by its ID.

    This endpoint allows deletion of a specific prescription using its unique identifier.

    Args:
        prescription_id: The UUID of the prescription to delete.
        db: The database session for performing the operation.

    Raises:
        HTTPException: If the prescription is not found or if there's an unexpected error.
    """
    try:
        deleted = await delete_prescription(db, prescription_id)
        if not deleted:
            logger.warning(f"Prescription with ID: {prescription_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID: {prescription_id} not found",
            )
        logger.info(f"Prescription with ID: {prescription_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prescription deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting the prescription.",
        ) from e
