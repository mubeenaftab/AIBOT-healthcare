from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from src.config.settings.logger_config import logger
from src.utilities.notification_service import notification_manager



async def connect_websocket(websocket: WebSocket, doctor_id: UUID) -> None:
    """
    Handle WebSocket connection for real-time notifications.

    Args:
        websocket (WebSocket): WebSocket connection to be managed.
        doctor_id (UUID): Unique identifier of the doctor.
    """
    await notification_manager.connect(websocket, doctor_id)
    try:
        while True:
            await websocket.receive_text()
            logger.info(f"text retrieved: {websocket.receive_text()}")
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket, doctor_id)
        logger.info(f"WebSocket disconnected for doctor_id: {doctor_id}")
