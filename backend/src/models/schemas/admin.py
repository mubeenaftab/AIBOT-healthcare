from pydantic import UUID4

from src.models.schemas.user import UserCreate, UserBase

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


class AdminCreate(UserCreate):
    """
    Schema for creating a new admin user.

    This class inherits from UserCreate without adding any new fields.
    It can be extended in the future if needed.
    """

    pass
