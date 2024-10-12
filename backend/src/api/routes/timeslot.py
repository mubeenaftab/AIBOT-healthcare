"""
Imports for managing time slot functionality in the FastAPI application.
Includes routing, dependency injection, and database interactions.

- UUID: Provides support for universally unique identifiers.
- APIRouter: Facilitates the creation of API routes.
- Depends: Enables dependency injection for request handling.
- HTTPException: Exception class for returning HTTP error responses.
- status: Contains HTTP status codes.
- AsyncSession: Asynchronous database session management for SQLAlchemy.
- logger: Application logging configuration.
- ErrorResponse: Schema for standardized error responses.
- TimeSlot, TimeSlotCreate: Pydantic schemas for time slot data handling.
- get_available_time_slots_from_db: Function to retrieve available time slots from the database.
- create_time_slot: Function to create a new time slot in the database.
- get_db: Dependency to obtain a database session.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.db.user import Doctor
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.timeslot import TimeSlot, TimeSlotCreate, TimeSlotResponse
from src.repository.crud.timeslot import (
    create_time_slot,
    get_available_time_slots_from_db,
    get_timeslot_by_doctor_id_from_db,
)
from src.repository.database import get_db
from src.securities.verification.credentials import get_current_user

router = APIRouter()


@router.post(
    "/create/timeslot",
    response_model=TimeSlot,
    responses={500: {"model": ErrorResponse}},
)
async def register_time_slot(
    time_slot: TimeSlotCreate,
    current_user: Doctor = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeSlot:
    """
    Register a new time slot for the currently logged-in doctor.

    Args:
        time_slot (TimeSlotCreate): The time slot data for registration.
        current_user (Doctor): The currently logged-in doctor.
        db (AsyncSession): The database session.

    Returns:
        TimeSlot: The registered time slot.

    Raises:
        HTTPException: If there's an error during time slot creation.
    """
    try:
        logger.info(
            f"Attempting to register time slot for doctor ID: {current_user.user_id}"
        )

        db_time_slot = await create_time_slot(
            db, time_slot=time_slot, doctor_id=current_user.user_id
        )
        logger.info(
            f"Time slot registered successfully with ID: {db_time_slot.time_slot_id}"
        )
        return TimeSlot.from_orm(db_time_slot)
    except Exception as e:
        logger.error(f"Unexpected error during time slot registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Error creating time slot",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/doctors/{doctor_id}/available_slots",
    response_model=list[TimeSlot],
    responses={404: {"model": ErrorResponse}},
)
async def get_available_time_slots(
    doctor_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[TimeSlot]:
    """
    Get available time slots for a specific doctor.

    Args:
        doctor_id (UUID): The unique identifier of the doctor.
        db (AsyncSession): The database session.

    Returns:
        List[TimeSlot]: A list of available time slots for the given doctor.

    Raises:
        HTTPException: If no available time slots are found.
    """
    slots = await get_available_time_slots_from_db(db, doctor_id)
    if not slots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail="No available time slots found for the doctor",
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )
    return [TimeSlot.from_orm(slot) for slot in slots]


@router.get(
    "/timeslots/{doctor_id}",
    response_model=TimeSlotResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_timeslot_by_doctor_id(
    doctor_id: str, db: AsyncSession = Depends(get_db)
) -> TimeSlotResponse:
    """
    Get a timeslot by doctor ID.

    Args:
        doctor_id (str): The ID of the doctor.
        db (AsyncSession): The database session.

    Returns:
        TimeslotResponse: The timeslot for the specified doctor.

    Raises:
        HTTPException: If the timeslot is not found.
    """
    timeslot = await get_timeslot_by_doctor_id_from_db(db, doctor_id)

    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeslot not found",
        )

    return TimeSlotResponse.from_orm(timeslot)
