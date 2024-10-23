from typing import Optional, Literal
from pydantic import BaseModel, Field, conint, field_validator, UUID4
from fastapi_pagination import Page
from src.models.schemas.user import UserCreate, UserBase

class DoctorCreate(UserCreate):
    """
    Schema for creating a new doctor user.

    Attributes:
        first_name (str): First name of the doctor (2-50 characters).
        last_name (str): Last name of the doctor (2-50 characters).
        specialization (str): Doctor's specialization (3-100 characters).
        phone_number (str): Phone number of the doctor (must be a valid Pakistani number).
        gender (str): Gender of the doctor, must be 'male', 'female', or 'other'.
        years_of_experience (int): Number of years the doctor has been practicing (1-70).
        consultation_fee (float): Consultation fee charged by the doctor (greater than 0).
    """
    
    first_name: str = Field(
        ..., min_length=2, max_length=50, description="First name of the doctor (2-50 characters)"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=50, description="Last name of the doctor (2-50 characters)"
    )
    specialization: str = Field(
        ..., min_length=3, max_length=100, description="Doctor's specialization (3-100 characters)"
    )
    phone_number: str = Field(..., description="Phone number of the doctor (must be a valid Pakistani number)")
    gender: Literal["male", "female", "other"] = Field(
        ..., description="Gender of the doctor, must be 'male', 'female', or 'other'"
    )
    years_of_experience: conint(ge=1, le=70) = Field(
        ..., description="Number of years the doctor has been practicing (1-70)"
    )
    consultation_fee: conint(gt=0) = Field(
        ..., description="Consultation fee charged by the doctor (greater than 0)"
    )

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
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value

class Doctor(UserBase):
    """
    Schema representing a doctor user.

    Attributes:
        user_id (UUID4): The unique identifier for the doctor user.
        first_name (str): First name of the doctor (2-50 characters).
        last_name (str): Last name of the doctor (2-50 characters).
        specialization (str): Doctor's specialization (3-100 characters).
        phone_number (str): Phone number of the doctor (must be a valid Pakistani number).
        gender (str): Gender of the doctor, must be 'male', 'female', or 'other'.
        years_of_experience (int): Number of years the doctor has been practicing (1-70).
        consultation_fee (float): Consultation fee charged by the doctor (greater than 0).
    """

    user_id: UUID4
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    specialization: str = Field(..., min_length=3, max_length=100)
    phone_number: str = Field(...)
    gender: Literal["male", "female", "other"] = Field(...)
    years_of_experience: conint(ge=1, le=70) = Field(...)
    consultation_fee: conint(gt=0) = Field(...)

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
                "Phone number must be a valid Pakistani number starting with '03' and exactly 11 digits long"
            )
        return value

    class Config:
        """Configuration for the Doctor model."""
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


from pydantic import BaseModel, Field, EmailStr, conint, validator
from typing import Optional, Literal

class DoctorUpdate(BaseModel):
    """
    Schema for updating doctor details.

    Attributes:
        password (Optional[str]): New password for the doctor, if changing.
        first_name (Optional[str]): First name of the doctor.
        last_name (Optional[str]): Last name of the doctor.
        specialization (Optional[str]): Doctor's specialization.
        phone_number (Optional[str]): Phone number of the doctor.
        gender (Optional[str]): Gender of the doctor, must be 'male', 'female', or 'other'.
        years_of_experience (Optional[int]): Updated years of experience (1-70).
        consultation_fee (Optional[float]): Updated consultation fee (greater than 0).
        email (Optional[str]): Email address of the doctor, must be a valid email.
        city (Optional[str]): City of the doctor, must contain only letters and spaces.
    """
    
    password: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    specialization: Optional[str]
    phone_number: Optional[str]
    gender: Optional[Literal["male", "female", "other"]]
    years_of_experience: Optional[conint(ge=1, le=70)]
    consultation_fee: Optional[conint(gt=0)]
    email: Optional[EmailStr] = Field(None, description="A valid email address for the doctor")
    city: Optional[str] = Field(None, description="City must contain only letters and spaces")

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
        if value and not value.replace(" ", "").isalpha():
            raise ValueError("City must only contain letters and spaces")
        return value

    class Config:
        orm_mode = True


PagedDoctor = Page[Doctor]
