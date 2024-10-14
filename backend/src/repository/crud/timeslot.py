"""
Imports for handling time slot updates in the FastAPI application.
Includes database operations and logging configuration.

- UUID: Provides support for universally unique identifiers.
- update: SQLAlchemy function to construct update statements.
- AsyncSession: Asynchronous database session management for SQLAlchemy.
- select: Function to construct SQL SELECT statements in a future context.
- logger: Application logging configuration.
- TimeSlotModel: ORM model for time slots.
- TimeSlotCreate: Pydantic schema for creating time slots.
"""

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.config.settings.logger_config import logger
from src.models.db.appointment import Appointment as AppointmentModel
from src.models.db.timeslot import TimeSlot as TimeSlotModel
from src.models.schemas.timeslot import TimeSlotCreate


async def create_time_slot(
    db: AsyncSession, time_slot: TimeSlotCreate, doctor_id: UUID
) -> TimeSlotModel:
    """
    Create a new time slot for a doctor.

    Args:
        db (AsyncSession): The database session for performing queries.
        time_slot (TimeSlotCreate): The time slot data including start time, end time, and status.
        doctor_id (UUID): The ID of the doctor for whom the time slot is being created.

    Returns:
        TimeSlotModel: The newly created time slot.

    Raises:
        Exception: If there is an error during the creation of the time slot.
    """
    try:
        db_time_slot = TimeSlotModel(
            doctor_id=doctor_id,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            status=time_slot.status,
        )
        db.add(db_time_slot)
        await db.commit()
        await db.refresh(db_time_slot)
        logger.info(
            f"Time slot created successfully with ID: {db_time_slot.time_slot_id}"
        )
        return db_time_slot
    except Exception as e:
        logger.error(f"Error creating time slot: {e}")
        raise


async def get_available_time_slots_from_db(
    db: AsyncSession, doctor_id: UUID
) -> list[TimeSlotModel]:
    """
    Fetch available time slots for a specific doctor from the database.

    Args:
        db (AsyncSession): The database session.
        doctor_id (UUID): The doctor's ID.

    Returns:
        List[TimeSlotModel]: List of available time slots for the doctor.
    """
    result = await db.execute(
        select(TimeSlotModel).where(
            TimeSlotModel.doctor_id == doctor_id, TimeSlotModel.status == "available"
        )
    )
    return result.scalars().all()


async def get_time_slot_by_id_from_db(
    db: AsyncSession, time_slot_id: UUID
) -> TimeSlotModel:
    """
    Fetch a time slot by its ID from the database.

    Args:
        db (AsyncSession): The database session.
        time_slot_id (UUID): The time slot ID.

    Returns:
        TimeSlotModel: The time slot with the given ID, if found.
    """
    result = await db.execute(
        select(TimeSlotModel).where(TimeSlotModel.time_slot_id == time_slot_id)
    )
    return result.scalar_one_or_none()


async def update_time_slot_status(
    db: AsyncSession, time_slot_id: UUID, status: str
) -> None:
    """
    Update the status of a time slot.

    Args:
        db (AsyncSession): The database session.
        time_slot_id (UUID): The time slot ID.
        status (str): The new status of the time slot.

    Returns:
        None
    """
    await db.execute(
        update(TimeSlotModel)
        .where(TimeSlotModel.time_slot_id == time_slot_id)
        .values(status=status)
    )
    await db.commit()


async def get_timeslot_by_doctor_id_from_db(db: AsyncSession, doctor_id: str):
    """
    Retrieve the first timeslot associated with a specific doctor from the database.

    This function queries the `TimeSlotModel` table in the database to find a timeslot
    that matches the given `doctor_id`. It returns the first matching timeslot if found,
    or `None` if no timeslot is associated with the doctor.

    Args:
        db (AsyncSession): The database session to execute the query.
        doctor_id (str): The ID of the doctor to filter timeslots.

    Returns:
        TimeSlotModel or None: The first matching timeslot object or `None` if not found.
    """
    result = await db.execute(
        select(TimeSlotModel).filter(TimeSlotModel.doctor_id == doctor_id)
    )
    return result.scalars().first()


async def delete_oldest_timeslot_by_doctor_and_patient(
    db: AsyncSession, appointment: AppointmentModel
) -> None:
    """
    Retrieve and delete the oldest time slot associated with a specific doctor and patient from the database.

    Args:
        db (AsyncSession): The database session to execute the query.
        appointment (AppointmentModel): The appointment containing the doctor and patient IDs.

    Returns:
        None
    """
    result = await db.execute(
        select(TimeSlotModel)
        .filter(TimeSlotModel.doctor_id == appointment.doctor_id)
        .order_by(TimeSlotModel.start_time.asc())
    )

    oldest_timeslot = result.scalars().first()

    if oldest_timeslot:
        await db.delete(oldest_timeslot)
        await db.commit()
        logger.info(f"Deleted time slot with ID: {oldest_timeslot.time_slot_id}")
