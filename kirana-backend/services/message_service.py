"""
Message routing service
Detects message type and routes to appropriate handler
"""

from typing import Dict, Any, Optional
from loguru import logger

from models.message import MessageInput, MessageResponse
from config.constants import MessageType


class MessageRouter:
    """Routes messages to appropriate handlers based on type"""

    def __init__(self):
        """Initialize message router"""
        logger.info("MessageRouter initialized")

    def detect_message_type(self, message: MessageInput) -> MessageType:
        """
        Detect message type from input

        Args:
            message: Input message

        Returns:
            Detected MessageType
        """
        # Message type is explicitly provided in the model
        return MessageType(message.message_type)

    def detect_image_subtype(
        self,
        message: MessageInput,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Detect whether image is shelf photo or parchi

        Args:
            message: Input message with image
            context: Additional context

        Returns:
            Subtype: "shelf_photo" or "parchi"
        """
        # Check for explicit hints in language field or content
        # (Since the actual model doesn't have metadata field)
        # For now, default to shelf photo (most common use case)
        # In production, this could use image classification
        logger.info("Image subtype not specified, defaulting to shelf_photo")
        return "shelf_photo"

    def extract_metadata(self, message: MessageInput) -> Dict[str, Any]:
        """
        Extract and normalize metadata from message

        Args:
            message: Input message

        Returns:
            Normalized metadata dict
        """
        metadata = {}

        # Add message type
        metadata["message_type"] = message.message_type

        # Add timestamps
        from datetime import datetime
        metadata["received_at"] = datetime.now().isoformat()

        # Add content length for analytics
        metadata["content_length"] = len(message.content)

        # Add language
        metadata["language"] = message.language

        return metadata

    def create_response(
        self,
        message_id: str,
        status: str = "completed",
        websocket_channel: Optional[str] = None
    ) -> MessageResponse:
        """
        Create standardized message response

        Args:
            message_id: Original message ID
            status: Processing status
            websocket_channel: WebSocket URL for updates

        Returns:
            MessageResponse
        """
        from datetime import datetime

        if not websocket_channel:
            websocket_channel = f"ws://localhost:8000/ws/store"

        return MessageResponse(
            message_id=message_id,
            status=status,
            websocket_channel=websocket_channel,
            timestamp=datetime.now().isoformat()
        )

    def validate_message(self, message: MessageInput) -> tuple[bool, Optional[str]]:
        """
        Validate message input

        Args:
            message: Input message

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if message has content
        if not message.content or len(message.content.strip()) == 0:
            return False, "Message content is required"

        # Validate store_id
        if not message.store_id:
            return False, "store_id is required"

        # Validate message type
        if message.message_type not in ["text", "image", "voice"]:
            return False, "message_type must be one of: text, image, voice"

        # For image and voice, validate base64 format
        if message.message_type in ["image", "voice"]:
            if not self._is_valid_base64(message.content):
                return False, f"Invalid base64 {message.message_type} data"

        return True, None

    def _is_valid_base64(self, data: str) -> bool:
        """
        Check if string is valid base64

        Args:
            data: String to check

        Returns:
            True if valid base64
        """
        import base64
        import binascii

        try:
            # Try to decode
            if isinstance(data, str):
                # Remove data URL prefix if present
                if "," in data:
                    data = data.split(",", 1)[1]

                decoded = base64.b64decode(data, validate=True)
                return len(decoded) > 0
            return False
        except (binascii.Error, ValueError):
            return False


# Singleton instance
_message_router: Optional[MessageRouter] = None


def get_message_router() -> MessageRouter:
    """Get or create MessageRouter singleton"""
    global _message_router
    if _message_router is None:
        _message_router = MessageRouter()
    return _message_router
