"""
This module defines the API routes for user authentication and creation in a FastAPI application.
It includes endpoints for logging in and creating new user accounts for admins, doctors, and patients.
These routes handle user authentication, issue JWT tokens, and interact with the database to create or verify users.

Routes:
    - POST /admin/login: Authenticate an admin and return a JWT token.
    - POST /doctor/login: Authenticate a doctor and return a JWT token.
    - POST /patient/login: Authenticate a patient and return a JWT token.

Dependencies:
    - `get_db`: Provides an async database session for each request.
    - `logger`: Used for logging important information during request processing.

Schemas:
    - `LoginRequest`: Schema for handling login requests, includes username and password.
    - `Token`: Schema for returning JWT tokens on successful login.
    - `ErrorResponse`: Schema for handling error responses, includes error details.

Functions:
    - `authenticate_admin`: Authenticates an admin user based on credentials.
    - `authenticate_doctor`: Authenticates a doctor user based on credentials.
    - `authenticate_patient`: Authenticates a patient user based on credentials.
    - `create_access_token`: Generates a JWT token after successful authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.schemas.auth_schema import LoginRequest, Token
from src.models.schemas.error_response import ErrorResponse
from src.repository.crud.admin import authenticate_admin
from src.repository.crud.doctor import authenticate_doctor
from src.repository.crud.patient import authenticate_patient
from src.repository.database import get_db
from src.securities.authorization.jwt import create_access_token
from src.utilities.constants import ErrorMessages

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Authenticate a user based on the role (patient, doctor, or admin) and provide an access token.

    Args:
        login_data (LoginRequest): The form data containing username, password, and role.
        db (AsyncSession): The database session used to validate user credentials.

    Returns:
        Token: A JWT access token for the authenticated user.

    Raises:
        HTTPException: If authentication fails due to invalid credentials or other errors.
    """
    try:
        logger.info(
            f"Attempting to authenticate user {login_data.username} as {login_data.role}"
        )

        # Authenticate based on the role
        if login_data.role == "patient":
            user = await authenticate_patient(
                db, login_data.username, login_data.password
            )
        elif login_data.role == "doctor":
            user = await authenticate_doctor(
                db, login_data.username, login_data.password
            )
        elif login_data.role == "admin":
            user = await authenticate_admin(
                db, login_data.username, login_data.password
            )
        else:
            logger.warning("Invalid role provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    detail=ErrorMessages.INVALID_ROLE.value,
                    status_code=status.HTTP_400_BAD_REQUEST,
                ).dict(),
            )

        # If authentication fails, return an unauthorized error
        if not user:
            logger.warning("Invalid credentials provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    detail=ErrorMessages.INVALID_CREDENTIALS.value,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                ).dict(),
            )

        # Generate a token with the username, user ID, and user type
        access_token = await create_access_token(
            data={
                "sub": user.username,
                "user_id": str(user.user_id),
                "type": login_data.role,
            }
        )

        logger.info(
            f"User authenticated successfully: {login_data.username} as {login_data.role}"
        )
        logger.info(
            f"User authenticated successfully: {login_data.username} as {login_data.role}"
        )
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=ErrorMessages.LOGIN_ERROR.value,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e
