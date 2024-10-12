"""
Imports BaseModel 4 from Pydantic for defining data models.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Base Pydantic model for defining Error data
    Attributes:
        detail will provide the description about the error
        status code will provide the error status code
    """

    detail: str
    status_code: int
