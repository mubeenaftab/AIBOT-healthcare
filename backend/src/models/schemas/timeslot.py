"""
Imports for defining data models and handling time-related data in the application.

- time: Provides support for time objects representing a specific time of day.
- UUID: Provides support for universally unique identifiers.
- BaseModel: Base class for creating Pydantic data models.
- Field: Function for defining model attributes with additional metadata.
"""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSlotBase(BaseModel):
    """
    Base schema for time slot data, used as a base class for other time slot schemas.
    """

    start_time: time = Field(..., description="Start time of the time slot")
    end_time: time = Field(..., description="End time of the time slot")
    status: str = Field(
        ..., description="Status of the time slot (available, booked, etc.)"
    )


class TimeSlotCreate(TimeSlotBase):
    """
    Schema for creating a time slot, extending the base time slot schema.
    """


class TimeSlot(TimeSlotBase):
    """
    Schema for a time slot, extending the base time slot schema.
    """

    time_slot_id: UUID

    class Config:
        """
        Configuration for the Pydantic model.

        Enables compatibility with ORM models by allowing the model to
        be populated from attributes of an ORM model instance.
        """

        from_attributes = True


class TimeSlotResponse(BaseModel):
    doctor_id: UUID
    start_time: time = Field(..., description="Start time of the time slot")
    end_time: time = Field(..., description="End time of the time slot")
    status: str = Field(..., description="Status of the time slot (available, booked, etc.)")
    time_slot_id: UUID

    class Config:
        """
        Configuration for the Pydantic model.

        Enables compatibility with ORM models by allowing the model to
        be populated from attributes of an ORM model instance.
        """

        from_attributes = True
