from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.reminder import Reminder as ReminderModel
from src.models.db.prescription import Prescription as PrescriptionModel
from src.models.schemas.prescription import PrescriptionCreate, PrescriptionUpdate
from src.models.schemas.reminder import ReminderStatus



async def create_prescription(
    db: AsyncSession, prescription_data: PrescriptionCreate, doctor_id: UUID
) -> PrescriptionModel:
    """
    Create a new prescription in the database by the current doctor.

    Args:
        db (AsyncSession): The database session.
        prescription_data (PrescriptionCreate): The prescription data to create.
        doctor_id (UUID): The ID of the doctor creating the prescription.

    Returns:
        PrescriptionModel: The created prescription object.

    Raises:
        Exception: If there is an error during the prescription creation.
    """
    from src.repository.crud.reminder import create_reminders_for_prescription

    try:
        new_prescription = PrescriptionModel(
            medication_name=prescription_data.medication_name,
            dosage=prescription_data.dosage,
            frequency=prescription_data.frequency,
            duration=prescription_data.duration,
            instructions=prescription_data.instructions,
            patient_id=prescription_data.patient_id,
            doctor_id=doctor_id,
        )
        db.add(new_prescription)
        await db.commit()
        await db.refresh(new_prescription)
        logger.info(
            f"Prescription created successfully with ID: {new_prescription.prescription_id}"
        )

        # Optional: Create reminders for the prescription if necessary
        await create_reminders_for_prescription(db, new_prescription)

        return new_prescription
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")
        await db.rollback()
        raise


async def get_prescription(
    db: AsyncSession, prescription_id: UUID
) -> PrescriptionModel:
    """
    Retrieve a prescription by its ID.

    Args:
        db (AsyncSession): The database session.
        prescription_id (UUID): The ID of the prescription to retrieve.

    Returns:
        PrescriptionModel: The retrieved prescription object.

    Raises:
        Exception: If there is an error during the retrieval.
    """
    try:
        result = await db.execute(
            select(PrescriptionModel).where(
                PrescriptionModel.prescription_id == prescription_id
            )
        )
        prescription = result.scalars().first()
        if prescription is None:
            logger.warning(f"Prescription with ID {prescription_id} not found")
        return prescription
    except Exception as e:
        logger.error(f"Error retrieving prescription: {e}")
        raise


async def update_prescription(
    db: AsyncSession, prescription_id: UUID, prescription_data: PrescriptionUpdate
) -> PrescriptionModel:
    """
    Update an existing prescription in the database.

    Args:
        db (AsyncSession): The database session.
        prescription_id (UUID): The ID of the prescription to update.
        prescription_data (PrescriptionUpdate): The updated prescription data.

    Returns:
        PrescriptionModel: The updated prescription object.

    Raises:
        Exception: If there is an error during the update or if the prescription does not exist.
    """
    try:
        stmt = (
            update(PrescriptionModel)
            .where(PrescriptionModel.prescription_id == prescription_id)
            .values(**prescription_data.dict(exclude_unset=True))
            .execution_options(synchronize_session="fetch")
        )
        result = await db.execute(stmt)
        await db.commit()
        if result.rowcount == 0:
            logger.warning(
                f"Prescription with ID {prescription_id} not found for update"
            )
            raise HTTPException(status_code=404, detail="Prescription not found")
        logger.info(f"Prescription with ID {prescription_id} updated successfully")
        return await get_prescription(db, prescription_id)
    except Exception as e:
        logger.error(f"Error updating prescription: {e}")
        await db.rollback()
        raise


async def delete_prescription(db: AsyncSession, prescription_id: UUID) -> bool:
    """
    Delete a prescription from the database.

    Args:
        db (AsyncSession): The database session.
        prescription_id (UUID): The ID of the prescription to delete.

    Returns:
        bool: True if the prescription was deleted, False otherwise.

    Raises:
        Exception: If there is an error during the deletion.
    """
    try:
        stmt = delete(PrescriptionModel).where(
            PrescriptionModel.prescription_id == prescription_id
        )
        result = await db.execute(stmt)
        await db.commit()
        if result.rowcount == 0:
            logger.warning(
                f"Prescription with ID {prescription_id} not found for deletion"
            )
            return False
        logger.info(f"Prescription with ID {prescription_id} deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Error deleting prescription: {e}")
        await db.rollback()
        raise


async def get_prescription_by_patient_id(patient_id: UUID, db: AsyncSession):
    try:
        query = select(PrescriptionModel).where(
            PrescriptionModel.patient_id == patient_id
        )
        result = await db.execute(query)
        prescription = result.scalars().first()

        if not prescription:
            return None

        return prescription

    except Exception as e:
        logger.error(f"Error fetching prescription for patient {patient_id}: {e}")
        return None


async def mark_prescription_inactive(
    db: AsyncSession, prescription_id: UUID
) -> Optional[PrescriptionModel]:
    """
    Mark an existing prescription as inactive in the database.

    Args:
        db (AsyncSession): The database session.
        prescription_id (UUID): The ID of the prescription to mark as inactive.

    Returns:
        Optional[PrescriptionModel]: The updated prescription object if successful, None if not found.

    """
    try:
        stmt = (
            update(PrescriptionModel)
            .where(PrescriptionModel.prescription_id == prescription_id)
            .values(is_active=False)
            .execution_options(synchronize_session="fetch")
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            logger.warning(
                f"Prescription with ID {prescription_id} not found for update"
            )
            return None

        logger.info(
            f"Prescription with ID {prescription_id} marked as inactive successfully"
        )

        return await get_prescription(db, prescription_id)

    except Exception as e:
        logger.error(f"Error marking prescription as inactive: {e}")
        await db.rollback()
        return None

async def get_prescriptions_for_appointment(
    db: AsyncSession, patient_id: int, doctor_id: int
) -> list[PrescriptionModel]:
    """
    Retrieve all prescriptions for the specified patient and doctor.

    Args:
        db (AsyncSession): The database session to execute queries.
        patient_id (int): The ID of the patient.
        doctor_id (int): The ID of the doctor.

    Returns:
        list[PrescriptionModel]: A list of prescriptions.
    """
    prescriptions = await db.execute(
        select(PrescriptionModel)
        .where(PrescriptionModel.patient_id == patient_id)
        .where(PrescriptionModel.doctor_id == doctor_id)
    )
    return prescriptions.scalars().all()

async def get_inactive_prescriptions_without_active_reminders(
    db: AsyncSession, prescriptions: list[PrescriptionModel]
) -> list[PrescriptionModel]:
    """
    Filter prescriptions that do not have active reminders.

    Args:
        db (AsyncSession): The database session to execute queries.
        prescriptions (list[PrescriptionModel]): The list of prescriptions to check.

    Returns:
        list[PrescriptionModel]: A list of prescriptions that don't have active reminders.
    """
    inactive_prescriptions = []
    for prescription in prescriptions:
        if prescription.is_active:
            active_reminders = await db.execute(
                select(ReminderModel)
                .where(ReminderModel.prescription_id == prescription.prescription_id)
                .where(ReminderModel.status == ReminderStatus.ACTIVE)
            )
            if not active_reminders.scalars().first():
                inactive_prescriptions.append(prescription)
    return inactive_prescriptions