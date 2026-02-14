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
                event=WebSocketEventType.CONNECTION_ESTABLISHED,
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
        icon: Optional[str] = None,
        step_number: Optional[int] = None,
        title: Optional[str] = None
    ):
        """
        Send reasoning step event

        Args:
            store_id: Store identifier
            step_type: Type of reasoning step
            description: Step description
            details: Additional details
            icon: Optional emoji icon
            step_number: Step sequence number
            title: Step title (frontend field)
        """
        # Generate title from step_type if not provided
        if title is None:
            title = step_type.replace("_", " ").title()

        # Default icon based on step type
        if icon is None:
            icon_map = {
                "SHELF_ANALYSIS": "🔍",
                "PARCHI_READING": "📝",
                "VOICE_PROCESSING": "🎤",
                "DEMAND_FORECAST": "📊",
                "PRICE_COMPARISON": "💰",
                "ORDER_GENERATION": "🛒",
                "ALERT_GENERATION": "⚠️",
                "COMPLETION": "✓"
            }
            icon = icon_map.get(step_type, "📌")

        timestamp = datetime.now().isoformat()

        event = ReasoningStepEvent(
            event=WebSocketEventType.REASONING_STEP,
            data={
                "step_number": step_number or 1,
                "step_type": step_type,
                "title": title,  # Frontend field
                "description": description,
                "icon": icon,
                "details": details or {},
                "timestamp": timestamp  # Frontend expects timestamp in data
            },
            timestamp=timestamp  # Also keep at root for backward compatibility
        )

        await self.send_event(store_id, event)

    async def send_chat_message(
        self,
        store_id: str,
        message: str,
        sender: str = "ai",
        message_type: str = "text",
        language: str = "hinglish",
        metadata: Optional[Dict] = None,
        message_id: Optional[str] = None
    ):
        """
        Send chat message event

        Args:
            store_id: Store identifier
            message: Message text
            sender: Message sender (ai/system)
            message_type: Type of message (text/markdown/image/order_card)
            language: Message language
            metadata: Additional metadata
            message_id: Unique message ID
        """
        import uuid

        timestamp = datetime.now().isoformat()

        # Generate message ID if not provided
        if message_id is None:
            message_id = f"msg_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        event = ChatMessageEvent(
            event=WebSocketEventType.CHAT_MESSAGE,
            data={
                "message_id": message_id,
                "sender": sender,  # "ai" or "system"
                "message_type": message_type,  # Frontend expects text/image/order_card
                "content": message,
                "formatted_content": message,  # Frontend field (same as content for now)
                "language": language,
                "metadata": metadata or {},
                "timestamp": timestamp  # Frontend expects timestamp in data
            },
            timestamp=timestamp  # Also keep at root for backward compatibility
        )

        await self.send_event(store_id, event)

    async def send_inventory_update(
        self,
        store_id: str,
        product_id: str,
        product_name: str,
        old_stock: int,
        new_stock: int,
        change: int,
        transaction_type: str,
        reason: str = "",
        days_of_stock: Optional[float] = None,
        status: Optional[str] = None,
        alerts: Optional[list] = None
    ):
        """
        Send inventory update event

        Args:
            store_id: Store identifier
            product_id: Product SKU ID
            product_name: Product name
            old_stock: Previous stock level
            new_stock: New stock level
            change: Stock change amount
            transaction_type: Type of transaction (sale/delivery/adjustment)
            reason: Reason for update
            days_of_stock: Days of stock remaining (frontend field)
            status: Stock status (healthy/warning/critical) (frontend field)
            alerts: Any alerts generated (frontend field)
        """
        # Calculate days_of_stock if not provided (estimate with 5 units/day average)
        if days_of_stock is None and new_stock >= 0:
            days_of_stock = new_stock / 5.0  # Simple estimate

        # Determine status if not provided
        if status is None:
            if days_of_stock is not None:
                if days_of_stock < 1.0:
                    status = "critical"
                elif days_of_stock < 3.0:
                    status = "warning"
                else:
                    status = "healthy"
            else:
                status = "healthy"

        # Generate alerts if not provided
        if alerts is None:
            alerts = []
            if status == "critical":
                alerts.append({
                    "type": "low_stock",
                    "message": f"{product_name} stock critically low - only {days_of_stock:.1f} days remaining",
                    "urgency": "high"
                })
            elif status == "warning":
                alerts.append({
                    "type": "low_stock",
                    "message": f"{product_name} running low - {days_of_stock:.1f} days remaining",
                    "urgency": "medium"
                })

        timestamp = datetime.now().isoformat()

        event = InventoryUpdateEvent(
            event=WebSocketEventType.INVENTORY_UPDATE,
            data={
                "product_id": product_id,
                "product_name": product_name,
                "old_stock": old_stock,
                "new_stock": new_stock,
                "change": change,
                "transaction_type": transaction_type,  # Backend uses this
                "change_type": "sold" if transaction_type == "sale" else "received",  # Frontend alias
                "reason": reason,
                "days_of_stock": round(days_of_stock, 1) if days_of_stock is not None else 0,  # Frontend field
                "status": status,  # Frontend field
                "alerts": alerts,  # Frontend field
                "timestamp": timestamp  # Frontend expects timestamp in data
            },
            timestamp=timestamp  # Also keep at root for backward compatibility
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
            order_data: Order details with items, total_cost, etc.
        """
        timestamp = datetime.now().isoformat()

        # Add frontend-compatible fields
        enhanced_order_data = {**order_data}

        # Rename total_savings to savings_vs_default for frontend
        if "total_savings" in enhanced_order_data:
            enhanced_order_data["savings_vs_default"] = enhanced_order_data["total_savings"]

        # Add upi_deeplink from first UPI link if available
        if "upi_links" in enhanced_order_data and len(enhanced_order_data["upi_links"]) > 0:
            enhanced_order_data["upi_deeplink"] = enhanced_order_data["upi_links"][0].get("upi_link", "")

        # Add valid_until (24 hours from now)
        from datetime import timedelta
        valid_until = datetime.now() + timedelta(hours=24)
        enhanced_order_data["valid_until"] = valid_until.isoformat()

        event = ProcurementOrderEvent(
            event=WebSocketEventType.PROCUREMENT_ORDER,
            data=enhanced_order_data,
            timestamp=timestamp
        )

        await self.send_event(store_id, event)

    async def send_udhaar_update(
        self,
        store_id: str,
        customer_name: str,
        old_amount: float,
        new_amount: float,
        transaction_date: str,
        transaction_type: str,
        total_outstanding: float
    ):
        """
        Send udhaar (credit) update event

        Args:
            store_id: Store identifier
            customer_name: Customer name
            old_amount: Previous outstanding amount
            new_amount: New outstanding amount
            transaction_date: Transaction date (ISO format)
            transaction_type: Type of transaction (credit_given/payment_received)
            total_outstanding: Total outstanding across all customers
        """
        from models.websocket import UdhaarUpdateEvent

        timestamp = datetime.now().isoformat()

        event = UdhaarUpdateEvent(
            event=WebSocketEventType.UDHAAR_UPDATE,
            data={
                "customer": customer_name,
                "old_amount": old_amount,
                "new_amount": new_amount,
                "change": new_amount - old_amount,
                "transaction_type": transaction_type,  # credit_given or payment_received
                "transaction": {
                    "date": transaction_date,
                    "type": transaction_type,
                    "amount": abs(new_amount - old_amount)
                },
                "total_outstanding": total_outstanding,
                "timestamp": timestamp  # Frontend expects timestamp in data
            },
            timestamp=timestamp  # Also keep at root for backward compatibility
        )

        await self.send_event(store_id, event)

    async def send_pnl_update(
        self,
        store_id: str,
        pnl_data: Dict
    ):
        """
        Send P&L update event

        Args:
            store_id: Store identifier
            pnl_data: P&L summary data (same format as /api/store/{store_id}/pnl response)
                Should include:
                - date: Date string
                - total_revenue: Total revenue
                - total_cogs: Total cost of goods sold
                - gross_profit: Gross profit
                - margin_pct: Profit margin percentage
                - cash_collected: Cash payments
                - upi_collected: UPI payments
                - credit_given: Credit sales
                - total_transactions: Number of transactions
                - items_sold: Total items sold
        """
        from models.websocket import PNLUpdateEvent

        timestamp = datetime.now().isoformat()

        # Add timestamp to data for frontend
        enhanced_pnl_data = {**pnl_data}
        enhanced_pnl_data["timestamp"] = timestamp

        event = PNLUpdateEvent(
            event=WebSocketEventType.PNL_UPDATE,
            data=enhanced_pnl_data,
            timestamp=timestamp
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
            event=WebSocketEventType.ERROR,
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
