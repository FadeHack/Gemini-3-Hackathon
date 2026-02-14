"""
WebSocket-related Pydantic models
Defines WebSocket event models for real-time communication
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from datetime import datetime


class WebSocketEvent(BaseModel):
    """Base WebSocket event model"""
    event: str = Field(..., description="Event type identifier")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    timestamp: str = Field(..., description="ISO timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "chat_message",
                "data": {
                    "message_id": "msg_ai_67890",
                    "sender": "ai",
                    "content": "Rajesh bhai, aapki Maggi ka stock khatam hone wala hai..."
                },
                "timestamp": "2026-02-14T14:30:00Z"
            }
        }


class ConnectionEvent(BaseModel):
    """WebSocket connection established event"""
    event: Literal["connection_established"] = "connection_established"
    data: Dict[str, Any] = Field(
        ...,
        description="Connection details"
    )
    timestamp: str


class ReasoningStepEvent(BaseModel):
    """AI reasoning step event"""
    event: Literal["reasoning_step"] = "reasoning_step"
    data: Dict[str, Any] = Field(
        ...,
        description="Reasoning step data with icon, title, description, details"
    )
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "event": "reasoning_step",
                "data": {
                    "step_number": 1,
                    "step_type": "SHELF_ANALYSIS",
                    "icon": "🔍",
                    "title": "Shelf Analysis",
                    "description": "Analyzing shelf photo...",
                    "details": {
                        "status": "in_progress"
                    }
                },
                "timestamp": "2026-02-14T14:30:01Z"
            }
        }


class ChatMessageEvent(BaseModel):
    """Chat message event"""
    event: Literal["chat_message"] = "chat_message"
    data: Dict[str, Any] = Field(
        ...,
        description="Chat message data"
    )
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "event": "chat_message",
                "data": {
                    "message_id": "msg_ai_20260214_143008",
                    "sender": "ai",
                    "message_type": "text",
                    "content": "Rajesh bhai, Navratri ke liye aapko 12 cheezein mangani chahiye...",
                    "language": "hinglish"
                },
                "timestamp": "2026-02-14T14:30:08Z"
            }
        }


class InventoryUpdateEvent(BaseModel):
    """Inventory update event"""
    event: Literal["inventory_update"] = "inventory_update"
    data: Dict[str, Any] = Field(
        ...,
        description="Inventory update data"
    )
    timestamp: str


class ProcurementOrderEvent(BaseModel):
    """Procurement order event"""
    event: Literal["procurement_order"] = "procurement_order"
    data: Dict[str, Any] = Field(
        ...,
        description="Procurement order data"
    )
    timestamp: str


class UdhaarUpdateEvent(BaseModel):
    """Udhaar (credit) update event"""
    event: Literal["udhaar_update"] = "udhaar_update"
    data: Dict[str, Any] = Field(
        ...,
        description="Credit ledger update data"
    )
    timestamp: str


class PNLUpdateEvent(BaseModel):
    """P&L update event"""
    event: Literal["pnl_update"] = "pnl_update"
    data: Dict[str, Any] = Field(
        ...,
        description="P&L summary data"
    )
    timestamp: str


class ErrorEvent(BaseModel):
    """Error event"""
    event: Literal["error"] = "error"
    data: Dict[str, Any] = Field(
        ...,
        description="Error details with type, message, fallback action"
    )
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "event": "error",
                "data": {
                    "error_type": "gemini_api_error",
                    "error_code": "GEMINI_TIMEOUT",
                    "message": "Gemini API request timed out",
                    "user_message": "Rajesh bhai, thoda technical issue aa raha hai. Kripya dobara try karein.",
                    "fallback_action": "retry",
                    "retry_count": 1,
                    "max_retries": 3
                },
                "timestamp": "2026-02-14T14:30:15Z"
            }
        }


# Client → Server events

class UserMessageEvent(BaseModel):
    """User message via WebSocket"""
    event: Literal["user_message"] = "user_message"
    data: Dict[str, Any] = Field(
        ...,
        description="User message data (alternative to REST API)"
    )


class HeartbeatEvent(BaseModel):
    """Heartbeat to keep connection alive"""
    event: Literal["heartbeat"] = "heartbeat"
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Heartbeat data (usually empty or timestamp)"
    )


class DisconnectEvent(BaseModel):
    """Graceful disconnect"""
    event: Literal["disconnect"] = "disconnect"
    data: Dict[str, Any] = Field(
        ...,
        description="Disconnect reason and timestamp"
    )
