"""
Message-related Pydantic models
Defines API request/response models for message endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class MessageInput(BaseModel):
    """Input message from frontend"""
    store_id: str = Field(..., description="Store identifier")
    message_type: Literal["text", "image", "voice"] = Field(
        ...,
        description="Type of message content"
    )
    content: str = Field(
        ...,
        description="Message content (text, base64 image, or base64 audio)"
    )
    language: Optional[str] = Field(
        "hinglish",
        description="Language preference: hinglish, hindi, kannada, tamil"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata (e.g., image_type: 'shelf' or 'parchi')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "sharma_general_store",
                "message_type": "text",
                "content": "Maggi ka stock kitna hai?",
                "language": "hinglish"
            }
        }


class MessageResponse(BaseModel):
    """Response after message submission"""
    message_id: str = Field(..., description="Unique message identifier")
    status: Literal["processing", "completed", "error"] = Field(
        ...,
        description="Processing status"
    )
    websocket_channel: str = Field(
        ...,
        description="WebSocket URL for real-time updates"
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of message receipt"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_20260214_143000",
                "status": "processing",
                "websocket_channel": "ws://localhost:8000/ws/sharma_general_store",
                "timestamp": "2026-02-14T14:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error code or type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "invalid_message_type",
                "message": "message_type must be one of: text, image, voice",
                "timestamp": "2026-02-14T14:30:00Z"
            }
        }
