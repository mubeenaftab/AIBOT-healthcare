from typing import List

import pendulum
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from src.config.settings.logger_config import logger
from src.models.db.prescription import Prescription as PrescriptionModel
from src.models.db.reminder import Reminder as ReminderModel
from src.models.schemas.reminder import ReminderStatus
from src.repository.crud.chat import enqueue_reminders
from src.repository.database import get_db

scheduler = AsyncIOScheduler()


async def trigger_reminder_task() -> None:
    """
    Asynchronously triggers the reminder task, which checks for active reminders
    in the database that are due. It fetches the reminders based on the current date
    and time, sends reminders for the respective prescriptions, and deletes the
    processed reminders from the database.

    This function:
    - Retrieves reminders that are active and due (i.e., their date and time have passed).
    - Fetches the associated prescription details for each reminder.
    - Enqueues the reminder message for the user.
    - Deletes the reminder from the database after processing.

    Args:
        None

    Raises:
        Exception: If there is any issue with database access or during reminder processing.
    """
    try:
        async for db in get_db():
            try:
                now = pendulum.now()
                current_date = now.date()
                current_time = now.time()

                reminders = await db.execute(
                    select(ReminderModel)
                    .where(ReminderModel.reminder_date <= current_date)
                    .where(ReminderModel.reminder_time <= current_time)
                    .where(ReminderModel.status == ReminderStatus.ACTIVE)
                )
                active_reminders: List[ReminderModel] = reminders.scalars().all()

                medication_names: List[str] = []
                for reminder in active_reminders:
                    prescription = await db.get(PrescriptionModel, reminder.prescription_id)
                    medication_names.append(prescription.medication_name)
                    
                    await db.delete(reminder)

                if medication_names:
                    await enqueue_reminders(medication_names)

                await db.commit()

                logger.info(f"Processed and deleted {len(active_reminders)} reminders.")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error processing reminders: {e}")
                raise
            finally:
                await db.close()
    except Exception as e:
        logger.error(f"Error occurred while getting database session: {e}")
        raise


def start_scheduler() -> None:
    """
    Start the APScheduler instance to trigger periodic tasks.

    The scheduler will run tasks like checking for active reminders every minute.
    """
    try:
        scheduler.add_job(trigger_reminder_task, "interval", minutes=1)
        scheduler.start()
        logger.info("Scheduler started successfully and will run tasks every minute.")
    except Exception as e:
        logger.error(f"Error starting the scheduler: {e}")
        raise
