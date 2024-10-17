"""
This module defines Pydantic schemas for user-related data in a healthcare application.

These schemas are used for validating and serializing user data, such as
user creation, login, and profile information, within the FastAPI application.
The module includes schemas for patients, doctors, and admins.

Imports:
    - re: For regular expression operations.
    - date, datetime: For handling date and time fields.
    - Page from fastapi_pagination: For paginated responses.
    - UUID4, BaseModel, Field, field_validator from pydantic: For data validation and serialization.
"""

import re
from datetime import date, datetime

from fastapi_pagination import Page
from pydantic import UUID4, BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Base schema for user data, used as a base class for other user schemas.

    Attributes:
        username (str): The username of the user. Must be 3-80 characters long,
                        start with a letter, and contain only letters, numbers,
                        underscores, and hyphens.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Username must be between 3 and 80 characters long",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """
        Validate the username format.

        Args:
            value (str): The username to validate.

        Returns:
            str: The validated username.

        Raises:
            ValueError: If the username format is invalid.
        """
        if value[0].isdigit():
            raise ValueError("Username cannot start with a number")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", value):
            raise ValueError(
                "Username must start with a letter and can only contain "
                "letters, numbers, underscores, and hyphens"
            )
        return value


class UserCreate(UserBase):
    """
    Schema for user creation, extending the base user schema.

    Attributes:
        password (str): The password for the user account. Must be at least 8
                        characters long and meet complexity requirements.
    """

    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate the password complexity.

        Args:
            password (str): The password to validate.

        Returns:
            str: The validated password.

        Raises:
            ValueError: If the password does not meet complexity requirements.
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

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate that the name does not start with a number.

        Args:
            value (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name starts with a number.
        """
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """
        Validate that the phone number is a valid Pakistani number.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' "
                "and exactly 11 digits long"
            )
        return value


class DoctorCreate(UserCreate):
    """
    Schema for creating a new doctor user.

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

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate that the name does not start with a number.

        Args:
            value (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name starts with a number.
        """
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """
        Validate that the phone number is a valid Pakistani number.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' "
                "and exactly 11 digits long"
            )
        return value


class AdminCreate(UserCreate):
    """
    Schema for creating a new admin user.

    This class inherits from UserCreate without adding any new fields.
    It can be extended in the future if needed.
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

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate that the name does not start with a number.

        Args:
            value (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name starts with a number.
        """
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """
        Validate that the phone number is a valid Pakistani number.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' "
                "and exactly 11 digits long"
            )
        return value

    class Config:
        """Configuration for the Patient model."""

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

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate that the name does not start with a number.

        Args:
            value (str): The name to validate.

        Returns:
            str: The validated name.

        Raises:
            ValueError: If the name starts with a number.
        """
        if value[0].isdigit():
            raise ValueError("Name cannot start with a number")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        """
        Validate that the phone number is a valid Pakistani number.

        Args:
            value (str): The phone number to validate.

        Returns:
            str: The validated phone number.

        Raises:
            ValueError: If the phone number is invalid.
        """
        if not value.startswith("03") or len(value) != 11 or not value.isdigit():
            raise ValueError(
                "Phone number must be a valid Pakistani number starting with '03' "
                "and exactly 11 digits long"
            )
        return value

    class Config:
        """Configuration for the Doctor model."""

        from_attributes = True


class Admin(UserBase):
    """
    Schema representing an admin user.

    Attributes:
        user_id (UUID4): The unique identifier for the admin user.
    """

    user_id: UUID4

    class Config:
        """Configuration for the Admin model."""

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
        """Configuration for the User model."""

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