"""
Image processing utilities
Base64 encoding/decoding, format validation, size checks
"""

import base64
import io
from typing import Tuple, Optional
from PIL import Image
from loguru import logger


# Supported image formats
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

# Max image size (10MB)
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def decode_base64_image(base64_data: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Decode base64 image data

    Args:
        base64_data: Base64 encoded image (with or without data URL prefix)

    Returns:
        Tuple of (success, image_bytes, error_message)
    """
    try:
        # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        # Decode base64
        image_bytes = base64.b64decode(base64_data, validate=True)

        # Check size
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            return False, None, f"Image too large ({len(image_bytes) / 1024 / 1024:.1f}MB > {MAX_IMAGE_SIZE_MB}MB)"

        return True, image_bytes, None

    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        return False, None, f"Invalid base64 image data: {str(e)}"


def validate_image_format(image_bytes: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate image format and get metadata

    Args:
        image_bytes: Raw image bytes

    Returns:
        Tuple of (is_valid, format, error_message)
    """
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))

        # Get format
        format_name = image.format

        if format_name not in SUPPORTED_IMAGE_FORMATS:
            return False, format_name, f"Unsupported image format: {format_name}. Supported: {SUPPORTED_IMAGE_FORMATS}"

        logger.debug(f"Valid image: {format_name}, size: {image.size}")
        return True, format_name, None

    except Exception as e:
        logger.error(f"Error validating image: {e}")
        return False, None, f"Invalid image file: {str(e)}"


def get_image_info(image_bytes: bytes) -> dict:
    """
    Get image metadata

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dict with image info (width, height, format, mode, size_bytes)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_bytes),
            "size_mb": round(len(image_bytes) / 1024 / 1024, 2)
        }

    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {}


def resize_image_if_needed(
    image_bytes: bytes,
    max_width: int = 2048,
    max_height: int = 2048,
    quality: int = 85
) -> Tuple[bytes, bool]:
    """
    Resize image if it exceeds max dimensions

    Args:
        image_bytes: Raw image bytes
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)

    Returns:
        Tuple of (image_bytes, was_resized)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        original_size = image.size

        # Check if resize needed
        if image.width <= max_width and image.height <= max_height:
            return image_bytes, False

        # Calculate new size maintaining aspect ratio
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save resized image
        output = io.BytesIO()
        save_format = image.format if image.format in SUPPORTED_IMAGE_FORMATS else "JPEG"

        if save_format == "JPEG":
            image.save(output, format=save_format, quality=quality, optimize=True)
        else:
            image.save(output, format=save_format, optimize=True)

        resized_bytes = output.getvalue()

        logger.info(
            f"Resized image from {original_size} to {image.size}, "
            f"size: {len(image_bytes) / 1024:.1f}KB → {len(resized_bytes) / 1024:.1f}KB"
        )

        return resized_bytes, True

    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image_bytes, False


def encode_image_to_base64(image_bytes: bytes, include_data_url: bool = False) -> str:
    """
    Encode image bytes to base64 string

    Args:
        image_bytes: Raw image bytes
        include_data_url: Whether to include data URL prefix

    Returns:
        Base64 encoded string
    """
    base64_str = base64.b64encode(image_bytes).decode('utf-8')

    if include_data_url:
        # Detect format
        try:
            image = Image.open(io.BytesIO(image_bytes))
            mime_type = f"image/{image.format.lower()}"
        except:
            mime_type = "image/jpeg"

        return f"data:{mime_type};base64,{base64_str}"

    return base64_str


def validate_and_process_image(
    base64_data: str,
    resize: bool = False,
    max_width: int = 2048,
    max_height: int = 2048
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Complete image validation and processing pipeline

    Args:
        base64_data: Base64 encoded image
        resize: Whether to resize if too large
        max_width: Maximum width for resize
        max_height: Maximum height for resize

    Returns:
        Tuple of (success, image_data, error_message)
        image_data contains: bytes, format, info, was_resized
    """
    # Decode base64
    success, image_bytes, error = decode_base64_image(base64_data)
    if not success:
        return False, None, error

    # Validate format
    is_valid, format_name, error = validate_image_format(image_bytes)
    if not is_valid:
        return False, None, error

    # Get info
    info = get_image_info(image_bytes)

    # Resize if needed
    was_resized = False
    if resize:
        image_bytes, was_resized = resize_image_if_needed(
            image_bytes,
            max_width=max_width,
            max_height=max_height
        )

    return True, {
        "bytes": image_bytes,
        "format": format_name,
        "info": info,
        "was_resized": was_resized
    }, None
