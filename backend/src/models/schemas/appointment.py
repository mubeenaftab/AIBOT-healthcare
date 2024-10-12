"""
Imports for data modeling and pagination in the FastAPI application.

- date, time: Provides classes for handling dates and times.
- Optional: Type hint for optional values in Python.
- UUID: Provides support for universally unique identifiers.
- Page: Pagination utility for handling paginated responses in FastAPI.
- BaseModel: Base class for creating Pydantic models.
- Field: Helper for defining fields in Pydantic models with validation and metadata.
"""

from datetime import date, time
from typing import Optional
from uuid import UUID

from fastapi_pagination import Page
from pydantic import BaseModel, Field


class AppointmentBase(BaseModel):
    """
    Schema representing the base fields for creating and updating an appointment.
    """

    appointment_date: date
    is_active: bool = Field(default=True)
    patient_id: UUID
    doctor_id: UUID


class AppointmentCreate(AppointmentBase):
    """
    Schema representing the fields required to create a new appointment.
    Inherits: AppointmentBase: Base schema with common appointment fields.
    """

    time_slot_id: UUID


class AppointmentUpdate(BaseModel):
    """
    Schema representing the fields required to update an appointment.
    All fields are optional to allow partial updates.
    """

    appointment_date: Optional[date]
    appointment_time: Optional[time]
    is_active: bool = Field(default=True)
    patient_id: Optional[UUID]
    doctor_id: Optional[UUID]


class Appointment(AppointmentBase):
    """
    Schema representing an appointment with a unique identifier.
    """

    appointment_id: UUID

    class Config:
        """
        Configuration for the Pydantic model.

        Enables compatibility with ORM models by allowing the model to
        be populated from attributes of an ORM model instance.
        """

        from_attributes = True


PagedAppointment = Page[Appointment]
