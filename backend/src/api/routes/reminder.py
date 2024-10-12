from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.settings.logger_config import logger
from src.models.db.prescription import Prescription as PrescriptionModel
from src.models.db.reminder import Reminder as ReminderModel
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.reminder import Reminder
from src.repository.crud.reminder import activate_reminders
from src.repository.database import get_db

router = APIRouter()


@router.put(
    "/prescriptions/{prescription_id}/reminders/activate",
    response_model=List[Reminder],
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def activate_reminders_for_prescription(
    prescription_id: UUID, db: AsyncSession = Depends(get_db)
) -> List[Reminder]:
    """
    Activate all reminders associated with a specific prescription.

    Args:
        prescription_id (UUID): The ID of the prescription for which to activate reminders.
        db (AsyncSession): The database session for the request.

    Returns:
        List[Reminder]: A list of reminders that were activated.

    Raises:
        HTTPException: If no reminders are found for the given prescription ID.
    """
    try:
        # Fetch prescription details to get frequency and duration
        prescription = await db.get(PrescriptionModel, prescription_id)
        if not prescription:
            logger.warning(f"No prescription found for ID: {prescription_id}")
            raise HTTPException(status_code=404, detail=f"Prescription not found for ID: {prescription_id}")

        # Fetch reminders associated with this prescription
        reminders = await db.execute(select(ReminderModel).where(ReminderModel.prescription_id == prescription_id))
        reminders_list = reminders.scalars().all()

        if not reminders_list:
            logger.warning(f"No reminders found for prescription ID: {prescription_id}")
            raise HTTPException(
                status_code=404, detail=f"No reminders found for this prescription ID: {prescription_id}"
            )

        # Activate reminders and assign dates
        activated_reminders = await activate_reminders(db, reminders_list, prescription)

        logger.info(f"Activated reminders for prescription ID: {prescription_id}")
        return activated_reminders
    except HTTPException as http_exc:
        logger.error(f"HTTP error occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error occurred while activating reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while activating status of reminder",
        ) from e
