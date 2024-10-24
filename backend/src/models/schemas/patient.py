import re

from datetime import date
from typing import Optional

from fastapi_pagination import Page
from pydantic import UUID4, BaseModel, Field, field_validator, EmailStr

from src.models.schemas.user import UserCreate, UserBase


class PatientCreate(UserCreate):
    """
    Schema for creating a new patient user.

    Attributes:
        first_name (str): First name of the patient (2-50 characters).
        last_name (str): Last name of the patient (2-50 characters).
        phone_number (str): Phone number of the patient (must be a valid Pakistani number).
        dob (date): Date of birth of the patient.
        gender (str): Gender of the patient ('male', 'female', 'other').
        blood_group (str): Valid blood group of the patient (e.g., 'A+', 'O-', etc.).
        emergency_contact (str): Emergency contact phone number (optional but must be a valid Pakistani number if provided).
    """

    first_name: str = Field(..., min_length=2, max_length=50, description="First name of the patient (2-50 characters)")
    last_name: str = Field(..., min_length=2, max_length=50, description="Last name of the patient (2-50 characters)")
    phone_number: str = Field(..., description="Phone number of the patient (must be a valid Pakistani number)")
    dob: date = Field(..., description="Date of birth of the patient")
    gender: str = Field(..., description="Gender of the patient ('male', 'female', or 'other')")
    blood_group: str = Field(..., description="Blood group of the patient (e.g., 'A+', 'O-', etc.)")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact number (optional)")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number", "emergency_contact")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if value and (not value.startswith("03") or len(value) != 11 or not value.isdigit()):
            raise ValueError("Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        valid_genders = ["male", "female", "other"]
        if value.lower() not in valid_genders:
            raise ValueError("Gender must be either 'male', 'female', or 'other'")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        valid_blood_groups = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
        if value.upper() not in valid_blood_groups:
            raise ValueError("Blood group must be one of the following: 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'")
        return value


class Patient(UserBase):
    """
    Schema representing a patient user.

    Attributes:
        user_id (UUID4): The unique identifier for the patient user.
        first_name (str): First name of the patient (2-50 characters).
        last_name (str): Last name of the patient (2-50 characters).
        phone_number (str): Phone number of the patient (must be a valid Pakistani number).
        dob (date): Date of birth of the patient.
        gender (str): Gender of the patient ('male', 'female', or 'other').
        blood_group (str): Blood group of the patient.
        emergency_contact (Optional[str]): Emergency contact phone number.
    """

    user_id: UUID4
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone_number: str = Field(...)
    dob: date
    gender: str
    blood_group: str
    emergency_contact: Optional[str]

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number", "emergency_contact")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if value and (not value.startswith("03") or len(value) != 11 or not value.isdigit()):
            raise ValueError("Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        valid_genders = ["male", "female", "other"]
        if value.lower() not in valid_genders:
            raise ValueError("Gender must be either 'male', 'female', or 'other'")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        valid_blood_groups = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
        if value.upper() not in valid_blood_groups:
            raise ValueError("Blood group must be one of the following: 'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'")
        return value

    class Config:
        """Configuration for the Patient model."""
        from_attributes=True


class PatientUpdate(BaseModel):
    """
    Schema for updating patient information.

    This schema allows partial updates of a patient's profile. Any field
    can be optional, meaning only the fields that need to be updated
    can be provided, while others remain unchanged.

    Attributes:
        email (Optional[str]): The email address of the patient, must be a valid email format.
        password (Optional[str]): The password for the patient account. If provided, it should meet the password complexity requirements.
        first_name (Optional[str]): The first name of the patient (2-50 characters).
        last_name (Optional[str]): The last name of the patient (2-50 characters).
        phone_number (Optional[str]): The phone number of the patient (must be a valid Pakistani number).
        city (Optional[str]): The city where the patient resides, containing only letters and spaces.
        dob (Optional[date]): The date of birth of the patient.
        gender (Optional[str]): The gender of the patient ('male', 'female', 'other').
        blood_group (Optional[str]): The blood group of the patient (e.g., 'A+', 'O-', etc.).
        emergency_contact (Optional[str]): The emergency contact phone number (must be a valid Pakistani number if provided).
    """

    email: Optional[EmailStr]
    password: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    city: Optional[str]
    dob: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    emergency_contact: Optional[str]


    @field_validator("city")
    @classmethod
    def validate_city(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate that the city contains only letters and spaces.

        Args:
            value (str): The city name to validate.

        Returns:
            str: The validated city name.

        Raises:
            ValueError: If the city contains invalid characters.
        """
        if value and not re.match(r"^[a-zA-Z\s]+$", value):
            raise ValueError("City must only contain letters and spaces")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate the gender field to ensure it is one of the accepted values.

        Args:
            value (str): The gender to validate.

        Returns:
            str: The validated gender.

        Raises:
            ValueError: If the gender is invalid.
        """
        if value and value not in ["male", "female", "other"]:
            raise ValueError("Gender must be 'male', 'female', or 'other'")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate the blood group to ensure it is a valid type.

        Args:
            value (str): The blood group to validate.

        Returns:
            str: The validated blood group.

        Raises:
            ValueError: If the blood group is invalid.
        """
        valid_blood_groups = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
        if value and value not in valid_blood_groups:
            raise ValueError("Invalid blood group")
        return value

    class Config:
        from_attributes = True




PagedPatient = Page[Patient]
