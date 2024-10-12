import uuid

from sqlalchemy import Date, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repository.database import Base


class Reminder(Base):  # type: ignore
    """
    Represents a reminder in the database.

    Attributes:
        reminder_id (UUID): The unique identifier for the reminder.
        prescription_id (UUID): Foreign key linking to a prescription.
        reminder_time (Time): The time for the reminder.
        status (str): The status of the reminder.
    """

    __tablename__ = "reminder"

    reminder_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    prescription_id: Mapped[UUID] = mapped_column(
        ForeignKey("prescription.prescription_id", ondelete="CASCADE"), nullable=False
    )
    reminder_time: Mapped[Time] = mapped_column(Time, nullable=False)
    reminder_date: Mapped[Date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    prescription = relationship("Prescription", back_populates="reminders")
