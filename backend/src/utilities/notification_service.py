import json
from uuid import UUID
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket

from src.config.settings.logger_config import logger

class NotificationManager:
    """
    Manages WebSocket connections for real-time notifications to doctors.

    Attributes:
        active_connections (Dict[UUID, Set[WebSocket]]): A dictionary mapping doctor IDs to sets of active WebSocket connections.
    """

    def __init__(self):
        """
        Initializes the NotificationManager with an empty dictionary for active connections.
        """
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        logger.info("NotificationManager initialized with empty active connections.")

    async def connect(self, websocket: WebSocket, doctor_id: UUID):
        """
        Establishes a WebSocket connection for a specific doctor.

        Args:
            websocket (WebSocket): The WebSocket connection to be accepted.
            doctor_id (UUID): The unique identifier of the doctor.
        
        Initializes a new set for the doctor in active connections if it doesn't exist,
        then adds the WebSocket connection to that set.
        """
        await websocket.accept()
        if doctor_id not in self.active_connections:
            self.active_connections[doctor_id] = set()
            logger.info(f"New connection set created for doctor_id: {doctor_id}")
        
        self.active_connections[doctor_id].add(websocket)
        logger.info(f"WebSocket connection established and added for doctor_id: {doctor_id}. Total connections: {len(self.active_connections[doctor_id])}")

    def disconnect(self, websocket: WebSocket, doctor_id: UUID):
        """
        Removes a WebSocket connection from the active connections for a specific doctor.

        Args:
            websocket (WebSocket): The WebSocket connection to be removed.
            doctor_id (UUID): The unique identifier of the doctor.

        Removes the WebSocket from the doctor's set of connections. If the set becomes empty, 
        it removes the doctor from active connections.
        """
        if doctor_id in self.active_connections and websocket in self.active_connections[doctor_id]:
            self.active_connections[doctor_id].remove(websocket)
            logger.info(f"WebSocket connection removed for doctor_id: {doctor_id}. Remaining connections: {len(self.active_connections[doctor_id])}")
            
            if not self.active_connections[doctor_id]:  # Remove doctor if no connections are left
                del self.active_connections[doctor_id]
                logger.info(f"No active connections left for doctor_id: {doctor_id}. Entry removed.")

    async def send_notification(self, doctor_id: UUID, message: str):
        """
        Sends a notification message to all active WebSocket connections for a specific doctor.

        Args:
            doctor_id (UUID): The unique identifier of the doctor.
            message (str): The notification message to be sent.
        """
        doctor_id_str = str(doctor_id)

        if doctor_id in self.active_connections:
            logger.info(f"Sending notification to doctor_id: {doctor_id_str}. Active connections: {len(self.active_connections[doctor_id])}")

            notification_payload = {
                "message": message,
                "doctor_id": doctor_id_str,
                "timestamp": datetime.now().isoformat()
            }

            # Convert to JSON string then parse back to dict to ensure serializability
            serializable_message = json.loads(json.dumps(notification_payload))

            for connection in self.active_connections[doctor_id]:
                try:
                    await connection.send_json(serializable_message)
                    logger.info(f"Notification sent to doctor_id: {doctor_id_str} on WebSocket connection.")
                except Exception as e:
                    logger.error(f"Error sending notification to doctor_id: {doctor_id_str} - {e}")
        else:
            logger.warning(f"No active connections found for doctor_id: {doctor_id_str}. Notification not sent.")



notification_manager = NotificationManager()
