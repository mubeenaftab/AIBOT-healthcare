from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db.user import Admin, Doctor, Patient
from src.repository.database import get_db
from src.securities.authorization.jwt import verify_token
from src.securities.hashing.hash import oauth2_scheme
from src.config.settings.logger_config import logger


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the current user based on the provided JWT token.

    The function decodes the JWT token to extract the user ID and user type.
    Based on the user type, it queries the database to fetch the corresponding user:
    - If the user type is "doctor", it fetches a Doctor instance.
    - If the user type is "patient", it fetches a Patient instance.
    - If the user type is "admin", it fetches an Admin instance.

    Args:
        token (str): The JWT token provided by the user.
        db (AsyncSession): The database session used to execute queries.

    Returns:
        Union[Doctor, Patient, Admin]: The current user instance based on the user type.

    Raises:
        HTTPException:
            - 403: If the user type is invalid.
            - 401: If the user is not found or if the token is invalid.
    """
    logger.debug(f"Authenticating user with token: {token[:10]}...")  # Log only first 10 chars for security
    
    try:
        payload = verify_token(token)
        if payload is None:
            logger.warning("Token verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("user_id")
        user_type = payload.get("type")
        logger.debug(f"Token payload - user_id: {user_id}, user_type: {user_type}")

        if user_type not in ["doctor", "patient", "admin"]:
            logger.warning(f"Invalid user type: {user_type}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user type",
            )

        # Query based on user type
        user_model = {"doctor": Doctor, "patient": Patient, "admin": Admin}[user_type]
        user = await db.execute(select(user_model).where(user_model.user_id == user_id))
        current_user = user.scalars().first()

        if current_user is None:
            logger.warning(f"User not found - user_id: {user_id}, user_type: {user_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        logger.debug(f"User authenticated successfully - user_id: {user_id}, user_type: {user_type}")
        return current_user

    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e
