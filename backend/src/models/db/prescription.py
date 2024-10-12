import uuid

from sqlalchemy import ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.repository.database import Base


class Prescription(Base):  # type: ignore
    """
    Represents a prescription in the database.

    Attributes:
        prescription_id (UUID): The unique identifier for the prescription.
        medication_name (str): The name of the medication.
        dosage (str): The dosage of the medication.
        frequency (int): The frequency of the medication intake (e.g., 1, 2, 3).
        duration (str): The duration for which the medication is prescribed.
        instructions (str): Additional instructions for the patient.
        patient_id (UUID): Foreign key linking to a patient.
        doctor_id (UUID): Foreign key linking to a doctor.
    """

    __tablename__ = "prescription"

    prescription_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    medication_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.user_id", ondelete="CASCADE"), nullable=False)
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("doctors.user_id", ondelete="CASCADE"), nullable=False)

    reminders = relationship("Reminder", back_populates="prescription")
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
