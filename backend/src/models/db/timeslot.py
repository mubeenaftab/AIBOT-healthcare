"""
Imports for defining database models and relationships using SQLAlchemy.

- uuid: Provides support for universally unique identifiers (UUID).
- ForeignKey: Defines foreign key constraints in SQLAlchemy models.
- String: Column type for string data in SQLAlchemy models.
- Time: Column type for time data in SQLAlchemy models.
- UUID: PostgreSQL-specific UUID type for SQLAlchemy.
- Mapped: Type hint for mapped columns in SQLAlchemy models.
- mapped_column: Function to define mapped columns in SQLAlchemy.
- relationship: Establishes relationships between SQLAlchemy models.
- Base: The declarative base class for defining SQLAlchemy models.
"""

import uuid

from sqlalchemy import ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repository.database import Base


class TimeSlot(Base):
    """
    Represents a time slot in the database.

    Attributes:
        time_slot_id (UUID): The unique identifier for the time slot.
        doctor_id (UUID): Foreign key linking to a doctor.
        start_time (Time): The start time of the time slot.
        end_time (Time): The end time of the time slot.
        status (str): The status of the time slot (available, booked, etc.).
    """

    __tablename__ = "time_slot"

    time_slot_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("doctors.user_id"), nullable=False)
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    end_time: Mapped[Time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    doctor = relationship("Doctor", back_populates="time_slots")
