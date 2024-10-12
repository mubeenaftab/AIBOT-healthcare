"""
This module defines Pydantic models for authentication-related data.

These models are used for validating and serializing authentication
data, such as access tokens and token-related information, within the
FastAPI application.

Imports:
    - BaseModel from Pydantic for creating data validation and serialization models.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """
    Pydantic model representing an authentication token.

    Attributes:
        access_token (str): The JWT access token issued to the user.
        token_type (str): The type of the token, typically 'bearer'.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Pydantic model representing data contained in an authentication token.

    Attributes:
        username (str | None): The username associated with the token.
                               This is optional and defaults to None.
    """

    username: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str
