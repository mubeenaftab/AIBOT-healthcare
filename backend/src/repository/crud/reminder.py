from uuid import UUID
from typing import List

import pendulum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings.logger_config import logger
from src.models.db.prescription import Prescription as PrescriptionModel
from src.models.db.reminder import Reminder as ReminderModel
from src.models.schemas.reminder import Reminder, ReminderCreate, ReminderStatus
from src.repository.crud.prescription import mark_prescription_inactive



async def create_reminders_for_prescription(db: AsyncSession, prescription: PrescriptionModel) -> None:
    """
    Create reminders for a given prescription in the database.

    This function generates reminders based on the frequency and duration
    specified in the prescription model. Reminders are initially set to
    inactive and will be associated with the prescription ID.

    Args:
        db (AsyncSession): The asynchronous database session to use for
            committing the reminders.
        prescription (PrescriptionModel): The prescription model containing
            details like frequency and duration to generate reminders.

    Raises:
        Exception: If there is an error while creating reminders, an
            exception is raised after rolling back the transaction.
    """
    try:
        frequency = prescription.frequency
        duration = prescription.duration

        for day in range(duration):
            reminder_times = generate_reminder_times(frequency)
            for reminder_time in reminder_times:
                new_reminder_data = ReminderCreate(
                    prescription_id=prescription.prescription_id,
                    reminder_time=pendulum.Time(**reminder_time),
                    reminder_date=None,  # Initially set to None
                    status=ReminderStatus.INACTIVE,
                )
                new_reminder = ReminderModel(**new_reminder_data.dict())
                db.add(new_reminder)

        await db.commit()
        mark_prescription_inactive(db, prescription.prescription_id)
        logger.info(f"Reminders created successfully for prescription ID: {prescription.prescription_id}")
    except Exception as e:
        logger.error(f"Error creating reminders: {e}")
        await db.rollback()
        raise


def generate_reminder_times(frequency: int) -> list[dict]:
    """
    Generate reminder times during the day based on the frequency.

    Args:
        frequency (int): The frequency of reminders per day (1, 2, or 3).

    Returns:
        list[dict]: List of reminder times (hours and minutes).
    """
    if frequency == 1:
        return [{"hour": 9, "minute": 0}]
    elif frequency == 2:
        return [{"hour": 9, "minute": 0}, {"hour": 18, "minute": 0}]
    elif frequency == 3:
        return [
            {"hour": 9, "minute": 0},
            {"hour": 13, "minute": 0},
            {"hour": 18, "minute": 0},
        ]
    else:
        raise ValueError(f"Unsupported frequency value: {frequency}")


async def activate_reminders(
    db: AsyncSession, reminders: List[ReminderModel], prescription: PrescriptionModel
) -> List[Reminder]:
    """
    Activate the given reminders by changing their status to ACTIVE and assigning reminder dates.

    Args:
        reminders (List[ReminderModel]): A list of reminders to activate.
        prescription (PrescriptionModel): The prescription details for calculating the reminder dates.

    Returns:
        List[Reminder]: The list of activated reminders.

    Raises:
        Exception: If there is an error during the reminder activation process.
    """
    try:
        current_date = pendulum.now().add(days=1)
        frequency = prescription.frequency
        duration = prescription.duration

        reminders_count = len(reminders)
        total_reminders_needed = frequency * duration

        if reminders_count != total_reminders_needed:
            logger.error(f"Mismatch: {reminders_count} reminders for prescription requiring {total_reminders_needed}.")

        reminder_index = 0
        for day in range(duration):
            for _ in range(frequency):
                if reminder_index < reminders_count:
                    reminder = reminders[reminder_index]
                    reminder.reminder_date = current_date.add(days=day).date()
                    reminder.status = ReminderStatus.ACTIVE
                    reminder_index += 1

        await db.commit()
        logger.info(f"Successfully activated {len(reminders)} reminders with dates.")
        return reminders

    except Exception as e:
        logger.error(f"Error activating reminders: {e}")
        await db.rollback()
        raise

async def update_reminder_times(prescription_id: UUID, new_times: list[dict], db: AsyncSession):
    """
    Update the reminder times for a given prescription.

    Args:
        prescription_id (int): The ID of the prescription to update reminders for.
        new_times (list[dict]): A list of new reminder times with 'hour' and 'minute'.
        db (AsyncSession): The database session to use.
    """
    try:
        reminders = await db.execute(
            select(ReminderModel)
            .where(ReminderModel.prescription_id == prescription_id)
            .order_by(ReminderModel.reminder_date)
        )
        reminders = reminders.scalars().all()
        logger.debug("reminders: ", reminders)

        if reminders:
            new_times_count = len(new_times)
            
            for i, reminder in enumerate(reminders):
                time_index = i % new_times_count
                reminder.reminder_time = pendulum.time(new_times[time_index]['hour'], new_times[time_index]['minute'])
            
            await db.commit()
            logger.info(f"Reminder times updated for prescription ID: {prescription_id}")
        else:
            logger.warning(f"No reminders found for prescription ID: {prescription_id}")
    
    except Exception as e:
        logger.error(f"Error updating reminders for prescription {prescription_id}: {e}")
        await db.rollback()
        raise
