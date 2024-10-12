"""
This module defines Pydantic schemas for user-related data.

These schemas are used for validating and serializing user data, such as
user creation, login, and profile information, within the FastAPI application.

Imports:
    - BaseModel from Pydantic for creating data validation and serialization models.
    - EmailStr from Pydantic for validating email addresses.
    - UUID4 from Pydantic for handling UUID fields.
    - Optional from typing for defining optional fields.
"""

import re
from datetime import date, datetime

from fastapi_pagination import Page

from pydantic import UUID4, BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Base schema for user data, used as a base class for other user schemas.

    Attributes:
        username (str): The username of the user.

    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Username must be between 3 and 80 characters long",
    )


class UserCreate(UserBase):
    """
    Schema for user creation, extending the base user schema.

    Attributes:
        password (str): The password for the user account.
    """

    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):
        """
        Validates the password to ensure it meets complexity requirements.

        Args:
            password (str): The password for the user account.

        Returns:
            str: The validated password if it meets the requirements.

        Raises:
            ValueError: If the password does not meet the complexity requirements.
        """
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")
        return password


class PatientCreate(UserCreate):
    """
    Schema for creating a new patient user.

    Inherits from UserCreate and adds fields specific to patient creation.

    Attributes:
        first_name (str): First name of the patient (2-50 characters).
        last_name (str): Last name of the patient (2-50 characters).
        phone_number (str): Phone number of the patient (must be a valid Pakistani number).
        dob (date): Date of birth of the patient.
    """

    first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name of the patient (2-50 characters)",
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Last name of the patient (2-50 characters)",
    )
    phone_number: str = Field(...)
    dob: date = Field(..., description="Date of birth of the patient")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        """
        Validate that the phone number is a valid Pakistani number.

        The phone number must start with '03', be exactly 11 digits long,
        and consist only of digits.

        Args:
            cls: The class being validated.
            value (str): The phone number to validate.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value


class DoctorCreate(UserCreate):
    """
    Schema for creating a new doctor user.

    Inherits from UserCreate and adds fields specific to doctor creation.

    Attributes:
        first_name (str): First name of the doctor (2-50 characters).
        last_name (str): Last name of the doctor (2-50 characters).
        specialization (str): Doctor's specialization (3-100 characters).
        phone_number (str): Phone number of the doctor (must be a valid Pakistani number).
    """

    first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name of the doctor (2-50 characters)",
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Last name of the doctor (2-50 characters)",
    )
    specialization: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Doctor's specialization (3-100 characters)",
    )
    phone_number: str = Field(...)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        """
        Validate that the phone number is a valid Pakistani number.

        The phone number must start with '03', be exactly 11 digits long,
        and consist only of digits.

        Args:
            cls: The class being validated.
            value (str): The phone number to validate.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value


class AdminCreate(UserCreate):
    """
    Schema for creating a new admin user.

    Inherits from UserCreate. Currently, it does not add any new fields,
    but it can be extended in the future.
    """

    pass


class Patient(UserBase):
    """
    Schema representing a patient user.

    Attributes:
        user_id (UUID4): The unique identifier for the patient user.
        first_name (str): First name of the patient (2-50 characters).
        last_name (str): Last name of the patient (2-50 characters).
        phone_number (str): Phone number of the patient (must be a valid Pakistani number).
        dob (date): Date of birth of the patient.
    """

    user_id: UUID4
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    phone_number: str = Field(...)
    dob: date

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        """
        Validate that the phone number is a valid Pakistani number.

        The phone number must start with '03', be exactly 11 digits long,
        and consist only of digits.

        Args:
            cls: The class being validated.
            value (str): The phone number to validate.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value

    class Config:
        from_attributes = True


class Doctor(UserBase):
    """
    Schema representing a doctor user.

    Attributes:
        user_id (UUID4): The unique identifier for the doctor user.
        first_name (str): First name of the doctor (2-50 characters).
        last_name (str): Last name of the doctor (2-50 characters).
        specialization (str): Doctor's specialization (3-100 characters).
        phone_number (str): Phone number of the doctor (must be a valid Pakistani number).
    """

    user_id: UUID4
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    specialization: str = Field(..., min_length=3, max_length=100)
    phone_number: str = Field(...)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        """
        Validate that the phone number is a valid Pakistani number.

        The phone number must start with '03', be exactly 11 digits long,
        and consist only of digits.

        Args:
            cls: The class being validated.
            value (str): The phone number to validate.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value

    class Config:
        from_attributes = True


class Admin(UserBase):
    """
    Schema representing an admin user.

    Attributes:
        user_id (UUID4): The unique identifier for the admin user.
    """

    user_id: UUID4

    class Config:
        from_attributes = True


class User(UserBase):
    """
    Schema for a user profile, extending the base user schema.

    Attributes:
        user_id (UUID4): The unique identifier for the user.
        is_active (bool): Indicates whether the user account is active.
        timestamp (datetime): The timestamp of when the user was created.
    """

    user_id: UUID4
    is_active: bool
    timestamp: datetime

    class Config:
        """
        Configuration for the Pydantic model.

        Enables compatibility with ORM models by allowing the model to
        be populated from attributes of an ORM model instance.
        """

        from_attributes = True


class DoctorResponse(BaseModel):
    """
    Schema for responding with doctor information.

    Attributes:
        first_name (str): First name of the doctor.
        last_name (str): Last name of the doctor.
        specialization (str): Doctor's specialization.
    """

    first_name: str
    last_name: str
    specialization: str


PagedDoctor = Page[Doctor]
PagedPatient = Page[Patient]
