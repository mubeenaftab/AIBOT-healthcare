"""
Imports for defining database models using SQLAlchemy.
Includes support for data types, relationships, and ORM mapping.

- uuid: Provides functionality for generating universally unique identifiers.
- Boolean: SQLAlchemy type for boolean values.
- Date: SQLAlchemy type for date values.
- ForeignKey: Defines a foreign key relationship between tables.
- UUID: PostgreSQL dialect for handling UUIDs.
- Mapped: Type for mapped attributes in SQLAlchemy ORM models.
- mapped_column: Function for defining mapped columns in ORM models.
- relationship: Establishes relationships between ORM models.
- Base: The declarative base class for SQLAlchemy models.
"""

import uuid

from sqlalchemy import Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.repository.database import Base


class Appointment(Base):
    """
    Represents an appointment in the database.

    Attributes:
        appointment_id (UUID): The unique identifier for the appointment.
        appointment_date (Date): The date of the appointment.
        appointment_time (Time): The time of the appointment.
        status (str): The status of the appointment.
        patient_id (UUID): Foreign key linking to a patient.
        doctor_id (UUID): Foreign key linking to a doctor.
    """

    __tablename__ = "appointment"

    appointment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    appointment_date: Mapped[Date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.user_id"), nullable=False
    )
    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("doctors.user_id"), nullable=False
    )

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
