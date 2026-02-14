"""
WebSocket service for real-time bidirectional communication
Manages WebSocket connections and event streaming
"""

import json
from typing import Dict, Set, Optional
from datetime import datetime
from loguru import logger

from fastapi import WebSocket, WebSocketDisconnect
from models.websocket import (
    WebSocketEvent,
    ReasoningStepEvent,
    ChatMessageEvent,
    InventoryUpdateEvent,
    ProcurementOrderEvent,
)
from config.constants import WebSocketEventType


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        """Initialize WebSocket manager"""
        # Store connections by store_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket, store_id: str):
        """
        Accept new WebSocket connection

        Args:
            websocket: WebSocket connection
            store_id: Store identifier
        """
        await websocket.accept()

        # Add to active connections
        if store_id not in self.active_connections:
            self.active_connections[store_id] = set()

        self.active_connections[store_id].add(websocket)

        logger.info(
            f"WebSocket connected for store={store_id}, "
            f"total_connections={len(self.active_connections[store_id])}"
        )

        # Send connection established event
        await self.send_event(
            store_id,
            WebSocketEvent(
                event=WebSocketEventType.CONNECTION_ESTABLISHED.value,
                timestamp=datetime.now().isoformat(),
                data={
                    "store_id": store_id,
                    "message": "Connected to KiranaGPT real-time stream",
                    "server_time": datetime.now().isoformat(),
                }
            ),
            websocket=websocket  # Send only to this connection
        )

    def disconnect(self, websocket: WebSocket, store_id: str):
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket connection to remove
            store_id: Store identifier
        """
        if store_id in self.active_connections:
            self.active_connections[store_id].discard(websocket)

            # Clean up empty store entries
            if len(self.active_connections[store_id]) == 0:
                del self.active_connections[store_id]

        logger.info(f"WebSocket disconnected for store={store_id}")

    async def send_event(
        self,
        store_id: str,
        event: WebSocketEvent,
        websocket: Optional[WebSocket] = None
    ):
        """
        Send event to WebSocket client(s)

        Args:
            store_id: Store identifier
            event: Event to send
            websocket: Specific websocket to send to (if None, broadcast to all)
        """
        if store_id not in self.active_connections:
            logger.warning(f"No active connections for store={store_id}")
            return

        # Serialize event
        event_data = event.model_dump()
        event_json = json.dumps(event_data, ensure_ascii=False)

        # Send to specific connection or broadcast
        connections = (
            [websocket]
            if websocket
            else list(self.active_connections[store_id])
        )

        for connection in connections:
            try:
                await connection.send_text(event_json)
                logger.debug(
                    f"Sent {event.event} to store={store_id}"
                )
            except Exception as e:
                logger.error(
                    f"Error sending to websocket for store={store_id}: {e}"
                )
                # Remove dead connection
                self.disconnect(connection, store_id)

    async def send_reasoning_step(
        self,
        store_id: str,
        step_type: str,
        description: str,
        details: Optional[Dict] = None,
        icon: Optional[str] = None
    ):
        """
        Send reasoning step event

        Args:
            store_id: Store identifier
            step_type: Type of reasoning step
            description: Step description
            details: Additional details
            icon: Optional emoji icon
        """
        event = ReasoningStepEvent(
            event=WebSocketEventType.REASONING_STEP.value,
            timestamp=datetime.now().isoformat(),
            data={
                "step_type": step_type,
                "description": description,
                "details": details or {},
                "icon": icon
            }
        )

        await self.send_event(store_id, event)

    async def send_chat_message(
        self,
        store_id: str,
        message: str,
        sender: str = "assistant",
        metadata: Optional[Dict] = None
    ):
        """
        Send chat message event

        Args:
            store_id: Store identifier
            message: Message text
            sender: Message sender (user/assistant)
            metadata: Additional metadata
        """
        event = ChatMessageEvent(
            event=WebSocketEventType.CHAT_MESSAGE.value,
            timestamp=datetime.now().isoformat(),
            data={
                "message": message,
                "sender": sender,
                "metadata": metadata or {}
            }
        )

        await self.send_event(store_id, event)

    async def send_inventory_update(
        self,
        store_id: str,
        product_id: str,
        old_stock: int,
        new_stock: int,
        change: int,
        transaction_type: str,
        alerts: Optional[list] = None
    ):
        """
        Send inventory update event

        Args:
            store_id: Store identifier
            product_id: Product SKU ID
            old_stock: Previous stock level
            new_stock: New stock level
            change: Stock change amount
            transaction_type: Type of transaction
            alerts: Any alerts generated
        """
        event = InventoryUpdateEvent(
            event=WebSocketEventType.INVENTORY_UPDATE.value,
            timestamp=datetime.now().isoformat(),
            data={
                "product_id": product_id,
                "old_stock": old_stock,
                "new_stock": new_stock,
                "change": change,
                "transaction_type": transaction_type,
                "alerts": alerts or []
            }
        )

        await self.send_event(store_id, event)

    async def send_procurement_order(
        self,
        store_id: str,
        order_data: Dict
    ):
        """
        Send procurement order event

        Args:
            store_id: Store identifier
            order_data: Order details
        """
        event = ProcurementOrderEvent(
            event=WebSocketEventType.PROCUREMENT_ORDER.value,
            timestamp=datetime.now().isoformat(),
            data=order_data
        )

        await self.send_event(store_id, event)

    async def send_error(
        self,
        store_id: str,
        error_message: str,
        error_code: Optional[str] = None
    ):
        """
        Send error event

        Args:
            store_id: Store identifier
            error_message: Error message
            error_code: Optional error code
        """
        event = WebSocketEvent(
            event=WebSocketEventType.ERROR.value,
            timestamp=datetime.now().isoformat(),
            data={
                "error": error_message,
                "code": error_code or "UNKNOWN_ERROR"
            }
        )

        await self.send_event(store_id, event)

    def get_connection_count(self, store_id: str) -> int:
        """
        Get number of active connections for a store

        Args:
            store_id: Store identifier

        Returns:
            Number of active connections
        """
        if store_id not in self.active_connections:
            return 0
        return len(self.active_connections[store_id])

    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all stores

        Returns:
            Total connection count
        """
        return sum(
            len(connections)
            for connections in self.active_connections.values()
        )


# Singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create WebSocketManager singleton"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
