import re
from typing import Optional
from uuid import UUID

from fastapi_pagination import Page
from pydantic import BaseModel, conint, Field, validator


class PrescriptionBase(BaseModel):
    """
    Schema representing the base fields for creating and updating a prescription.
    """

    medication_name: str = Field(..., min_length=2, max_length=100, description="Name of the medication")
    dosage: str = Field(..., description="Dosage in the format 'number mg/ml', e.g., '500 mg' or '10 ml'")
    frequency: conint(ge=1, le=3) = Field(..., description="Frequency of the medication intake per day (1 to 3 times per day)")
    duration: conint(ge=1, le=30) = Field(..., description="Duration for which the medication is prescribed (1 to 30)")
    instructions: Optional[str] = Field(None, max_length=255, description="Additional instructions for the patient")
    patient_id: UUID
    doctor_id: UUID
    is_active: bool = Field(True, description="Indicates if the prescription is active")

    @validator("dosage")
    @classmethod
    def validate_dosage(cls, value):
        dosage_pattern = re.compile(r"^\d+(\.\d+)?\s?(mg|ml)$")
        if not dosage_pattern.match(value):
            raise ValueError("Dosage must be in the format 'number mg' or 'number ml', e.g., '500 mg' or '10 ml'")
        return value


class PrescriptionCreate(PrescriptionBase):
    """
    Schema representing the fields required to create a new prescription.
    Inherits: PrescriptionBase: Base schema with common prescription fields.
    """


class PrescriptionUpdate(PrescriptionBase):
    """
    Schema representing the fields required to update a prescription.
    All fields are optional to allow partial updates.
    """

    medication_name: Optional[str] = Field(None, min_length=2, max_length=100)
    dosage: Optional[str] = Field(None)
    frequency: Optional[conint(ge=1, le=3)]
    duration: Optional[conint(ge=1, le=30)]
    instructions: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None, description="Indicates if the prescription is active")


class Prescription(PrescriptionBase):
    """
    Schema representing a prescription with a unique identifier.
    """

    prescription_id: UUID

    class Config:
        from_attributes = True


PagedPrescription = Page[Prescription]
