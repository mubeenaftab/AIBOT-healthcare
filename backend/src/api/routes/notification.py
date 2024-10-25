from uuid import UUID

from fastapi import APIRouter, WebSocket

from src.config.settings.logger_config import logger
from src.repository.crud.notification import connect_websocket


router = APIRouter()



@router.websocket("/ws/notifications/{doctor_id}")
async def websocket_endpoint(websocket: WebSocket, doctor_id: UUID):
    """
    WebSocket endpoint for real-time notifications for a specific doctor.

    Args:
        websocket (WebSocket): The WebSocket connection for the client.
        doctor_id (UUID): Unique identifier of the doctor.
    """
    logger.info(f"WebSocket connection initiated for doctor_id: {doctor_id}")
    await connect_websocket(websocket, doctor_id)
