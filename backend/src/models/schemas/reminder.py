from datetime import date, time
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi_pagination import Page
from pydantic import BaseModel, Field


class ReminderStatus(str, Enum):
    """
    Enum representing the possible statuses for a reminder.
    """

    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ReminderBase(BaseModel):
    """
    Schema representing the base fields for creating and updating a reminder.
    """

    prescription_id: UUID
    reminder_time: time = Field(..., description="Time for the reminder")
    reminder_date: Optional[date] = Field(None, description="Date for the reminder")
    status: ReminderStatus = Field(..., description="Status of the reminder")


class ReminderCreate(ReminderBase):
    """
    Schema representing the fields required to create a new reminder.
    Inherits: ReminderBase: Base schema with common reminder fields.
    """


class ReminderUpdate(BaseModel):
    """
    Schema representing the fields required to update a reminder.
    All fields are optional to allow partial updates.
    """

    prescription_id: Optional[UUID]
    reminder_time: Optional[time]
    reminder_date: Optional[date]
    status: Optional[ReminderStatus]


class Reminder(ReminderBase):
    """
    Schema representing a reminder with a unique identifier.
    """

    reminder_id: UUID

    class Config:
        """
        Configuration for the Pydantic model.

        Enables compatibility with ORM models by allowing the model to
        be populated from attributes of an ORM model instance.
        """

        from_attributes = True


PagedReminder = Page[Reminder]
