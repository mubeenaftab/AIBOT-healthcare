"""
This module defines Pydantic schemas for user-related data in a healthcare application.

These schemas are used for validating and serializing user data, such as
user creation, login, and profile information, within the FastAPI application.
The module includes schemas for patients, doctors, and admins.

Imports:
    - re: For regular expression operations.
    - datetime: For handling date and time fields.
    - Page from fastapi_pagination: For paginated responses.
    - UUID4, BaseModel, Field, field_validator from pydantic: For data validation and serialization.
"""

import re
from datetime import datetime

from pydantic import UUID4, BaseModel, Field, validator


class UserBase(BaseModel):
    """
    Base schema for user data, used as a base class for other user schemas.

    Attributes:
        username (str): The username of the user. Must be 3-80 characters long,
                        start with a letter, and contain only letters, numbers,
                        underscores, and hyphens.
        city (str): The city where the user lives, containing only letters and spaces.
    """

    username: str = Field(
        ..., min_length=3, max_length=80, description="Username must be between 3 and 80 characters long"
    )
    email: str = Field(..., description="A valid email address")
    city: str = Field(
        ..., description="City must contain only letters and spaces"
    )

    @validator("username")
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
    
    @validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """
        Validate the email format.

        Args:
            value (str): The email address to validate.

        Returns:
            str: The validated email address.

        Raises:
            ValueError: If the email format is invalid.
        """
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Invalid email format")
        return value

    @validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        """
        Validate that the city contains only letters and spaces.

        Args:
            value (str): The city name to validate.

        Returns:
            str: The validated city name.

        Raises:
            ValueError: If the city contains invalid characters.
        """
        if not re.match(r"^[a-zA-Z\s]+$", value):
            raise ValueError("City must only contain letters and spaces")
        return value


class UserCreate(UserBase):
    """
    Schema for user creation, extending the base user schema.

    Attributes:
        password (str): The password for the user account. Must be at least 8
                        characters long and meet complexity requirements.
    """

    password: str = Field(..., min_length=8)

    @validator("password")
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