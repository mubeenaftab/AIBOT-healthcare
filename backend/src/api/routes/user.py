"""
This module defines the API routes for user authentication and creation in a FastAPI application.
It includes endpoints for logging in and creating new user accounts for admins, doctors, and patients.
These routes handle user authentication, issue JWT tokens, and interact with the database to create or verify users.

Routes:
    - POST /admin/login: Authenticate an admin and return a JWT token.
    - POST /doctor/login: Authenticate a doctor and return a JWT token.
    - POST /patient/login: Authenticate a patient and return a JWT token.
    - POST /admin/signup: Create a new admin account.
    - POST /doctor/signup: Create a new doctor account.
    - POST /patient/signup: Create a new patient account.

Dependencies:
    - `get_db`: Provides an async database session for each request.
    - `logger`: Used for logging important information during request processing.

Schemas:
    - `LoginRequest`: Schema for handling login requests, includes username and password.
    - `Token`: Schema for returning JWT tokens on successful login.
    - `ErrorResponse`: Schema for handling error responses, includes error details.
    - `Admin`, `AdminCreate`: Schemas for admin data and creating new admins.
    - `Doctor`, `DoctorCreate`: Schemas for doctor data and creating new doctors.
    - `Patient`, `PatientCreate`: Schemas for patient data and creating new patients.

Functions:
    - `authenticate_admin`: Authenticates an admin user based on credentials.
    - `authenticate_doctor`: Authenticates a doctor user based on credentials.
    - `authenticate_patient`: Authenticates a patient user based on credentials.
    - `create_admin`: Creates a new admin account.
    - `create_doctor`: Creates a new doctor account.
    - `create_patient`: Creates a new patient account.
    - `create_access_token`: Generates a JWT token after successful authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings.logger_config import logger
from src.models.schemas.auth_schema import LoginRequest, Token
from src.models.schemas.error_response import ErrorResponse
from src.models.schemas.user import (
    Admin,
    AdminCreate,
    Doctor,
    DoctorCreate,
    Patient,
    PatientCreate,
)
from src.repository.crud.user import (
    authenticate_admin,
    authenticate_doctor,
    authenticate_patient,
    create_admin,
    create_doctor,
    create_patient,
    get_doctor_by_id_from_db,
    get_doctors_by_specialization_from_db,
    get_patient_by_id_from_db,
)
from src.repository.database import get_db
from src.securities.authorization.jwt import create_access_token

router = APIRouter()


@router.post(
    "/register/patient",
    response_model=Patient,
    responses={500: {"model": ErrorResponse}},
)
async def register_patient(
    patient: PatientCreate, db: AsyncSession = Depends(get_db)
) -> Patient:
    """
    Register a new patient.

    Args:
        patient (PatientCreate): The patient data for registration.
        db (Session): The database session.

    Returns:
        PatientSchema: The registered patient.

    Raises:
        HTTPException: If there's an error during patient creation.
    """
    try:
        logger.info(f"Attempting to register patient with username: {patient.username}")
        db_patient = await create_patient(db, patient)
        logger.info(f"Patient registered successfully with ID: {db_patient.user_id}")
        return Patient.from_orm(db_patient)
    except Exception as e:
        logger.error(f"Unexpected error during patient registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Patient already exists",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.post(
    "/register/doctor",
    response_model=Doctor,
    responses={500: {"model": ErrorResponse}},
)
async def register_doctor(
    doctor: DoctorCreate, db: AsyncSession = Depends(get_db)
) -> Doctor:
    """
    Register a new doctor.

    Args:
        doctor (DoctorCreate): The doctor data for registration.
        db (Session): The database session.

    Returns:
        DoctorSchema: The registered doctor.

    Raises:
        HTTPException: If there's an error during doctor creation.
    """
    try:
        logger.info(f"Attempting to register doctor with username: {doctor.username}")
        db_doctor = await create_doctor(db, doctor)
        logger.info(f"Doctor registered successfully with ID: {db_doctor.user_id}")
        return Doctor.from_orm(db_doctor)
    except Exception as e:
        logger.error(f"Unexpected error during doctor registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Doctor already exists",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.post(
    "/register/admin",
    response_model=Admin,
    responses={500: {"model": ErrorResponse}},
)
async def register_admin(
    admin: AdminCreate, db: AsyncSession = Depends(get_db)
) -> Admin:
    """
    Register a new admin.

    Args:
        admin (AdminCreate): The admin data for registration.
        db (Session): The database session.

    Returns:
        AdminSchema: The registered admin.

    Raises:
        HTTPException: If there's an error during admin creation.
    """
    try:
        logger.info(f"Attempting to register admin with username: {admin.username}")
        db_admin = await create_admin(db, admin)
        logger.info(f"Admin registered successfully with ID: {db_admin.user_id}")
        return Admin.from_orm(db_admin)
    except Exception as e:
        logger.error(f"Unexpected error during admin registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail="Error creating admin",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


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
                    detail="Invalid role specified.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                ).dict(),
            )

        # If authentication fails, return an unauthorized error
        if not user:
            logger.warning("Invalid credentials provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    detail="Invalid credentials",
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
                detail="Error logging in",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).dict(),
        ) from e


@router.get(
    "/doctors",
    response_model=list[Doctor],
    responses={404: {"model": ErrorResponse}},
)
async def get_doctors_by_specialization(
    specialization: str, db: AsyncSession = Depends(get_db)
) -> list[Doctor]:
    """
    Get a list of doctors based on specialization.

    Args:
        specialization (str): The specialization of the doctor.
        db (AsyncSession): The database session.

    Returns:
        List[Doctor]: A list of doctors with the specified specialization.

    Raises:
        HTTPException: If no doctors are found.
    """
    logger.debug(f"Searching for doctors with specialization: '{specialization}'")
    doctors = await get_doctors_by_specialization_from_db(db, specialization)
    if not doctors:
        logger.warning(f"No doctors found for specialization: '{specialization}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=f"No doctors found for the given specialization: '{specialization}'",
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )
    return [Doctor.from_orm(doctor) for doctor in doctors]


@router.get(
    "/patients/{patient_id}",
    response_model=Patient,
    responses={404: {"model": ErrorResponse}},
)
async def get_patient_by_id(
    patient_id: str, db: AsyncSession = Depends(get_db)
) -> Patient:
    """
    Get a patient by ID.

    Args:
        patient_id (str): The ID of the patient.
        db (AsyncSession): The database session.

    Returns:
        Patient: The patient with the specified ID.

    Raises:
        HTTPException: If the patient is not found.
    """
    logger.info(f"Fetching patient with ID: {patient_id}")

    patient = await get_patient_by_id_from_db(db, patient_id)

    if not patient:
        logger.warning(f"Patient with ID {patient_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail="Patient not found",
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )

    logger.info(f"Patient with ID {patient_id} found: {patient}")
    return Patient.from_orm(patient)


@router.get(
    "/doctors/{doctor_id}",
    response_model=Doctor,
    responses={404: {"model": ErrorResponse}},
)
async def get_doctor_by_id(
    doctor_id: str, db: AsyncSession = Depends(get_db)
) -> Doctor:
    """
    Get a doctor by ID.

    Args:
        doctor_id (str): The ID of the doctor.
        db (AsyncSession): The database session.

    Returns:
        Doctor: The doctor with the specified ID.

    Raises:
        HTTPException: If the doctor is not found.
    """
    logger.info(f"Fetching doctor with ID: {doctor_id}")

    doctor = await get_doctor_by_id_from_db(db, doctor_id)

    if not doctor:
        logger.warning(f"Doctor with ID {doctor_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail="Doctor not found",
                status_code=status.HTTP_404_NOT_FOUND,
            ).dict(),
        )

    logger.info(f"Doctor with ID {doctor_id} found: {doctor}")
    return Doctor.from_orm(doctor)
