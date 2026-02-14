"""
Audio processing utilities
Base64 encoding/decoding, format validation, duration checks
"""

import base64
import io
from typing import Tuple, Optional
from loguru import logger


# Supported audio formats (common MIME types)
SUPPORTED_AUDIO_FORMATS = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
    "audio/aac",
    "audio/m4a"
}

# Audio file signatures (magic bytes)
AUDIO_SIGNATURES = {
    b'RIFF': 'wav',
    b'ID3': 'mp3',
    b'\xff\xfb': 'mp3',
    b'\xff\xf3': 'mp3',
    b'\xff\xf2': 'mp3',
    b'OggS': 'ogg',
    b'fLaC': 'flac',
}

# Max audio size (25MB for voice messages)
MAX_AUDIO_SIZE_MB = 25
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024


def decode_base64_audio(base64_data: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Decode base64 audio data

    Args:
        base64_data: Base64 encoded audio (with or without data URL prefix)

    Returns:
        Tuple of (success, audio_bytes, error_message)
    """
    try:
        # Remove data URL prefix if present (e.g., "data:audio/wav;base64,")
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]

        # Decode base64
        audio_bytes = base64.b64decode(base64_data, validate=True)

        # Check size
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            return False, None, f"Audio too large ({len(audio_bytes) / 1024 / 1024:.1f}MB > {MAX_AUDIO_SIZE_MB}MB)"

        # Minimum size check (at least 100 bytes)
        if len(audio_bytes) < 100:
            return False, None, "Audio data too small to be valid"

        return True, audio_bytes, None

    except Exception as e:
        logger.error(f"Error decoding base64 audio: {e}")
        return False, None, f"Invalid base64 audio data: {str(e)}"


def detect_audio_format(audio_bytes: bytes) -> Optional[str]:
    """
    Detect audio format from file signature (magic bytes)

    Args:
        audio_bytes: Raw audio bytes

    Returns:
        Detected format string or None
    """
    # Check first 4 bytes against known signatures
    for signature, format_name in AUDIO_SIGNATURES.items():
        if audio_bytes.startswith(signature):
            return format_name

    # Check for MP4/M4A (AAC)
    if audio_bytes[4:8] == b'ftyp':
        return 'm4a'

    return None


def validate_audio_format(audio_bytes: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate audio format

    Args:
        audio_bytes: Raw audio bytes

    Returns:
        Tuple of (is_valid, format, error_message)
    """
    try:
        # Detect format
        format_name = detect_audio_format(audio_bytes)

        if not format_name:
            return False, None, "Could not detect audio format. Supported: wav, mp3, ogg, flac, aac, m4a"

        logger.debug(f"Valid audio: {format_name}, size: {len(audio_bytes) / 1024:.1f}KB")
        return True, format_name, None

    except Exception as e:
        logger.error(f"Error validating audio: {e}")
        return False, None, f"Invalid audio file: {str(e)}"


def get_audio_info(audio_bytes: bytes) -> dict:
    """
    Get audio metadata (basic info without decoding)

    Args:
        audio_bytes: Raw audio bytes

    Returns:
        Dict with audio info
    """
    try:
        format_name = detect_audio_format(audio_bytes)

        info = {
            "format": format_name,
            "size_bytes": len(audio_bytes),
            "size_kb": round(len(audio_bytes) / 1024, 2),
            "size_mb": round(len(audio_bytes) / 1024 / 1024, 2)
        }

        # Estimate duration for WAV files (rough estimate)
        if format_name == "wav" and len(audio_bytes) > 44:
            # WAV header is 44 bytes, sample rate at byte 24
            try:
                sample_rate = int.from_bytes(audio_bytes[24:28], byteorder='little')
                channels = int.from_bytes(audio_bytes[22:24], byteorder='little')
                bits_per_sample = int.from_bytes(audio_bytes[34:36], byteorder='little')

                if sample_rate > 0:
                    data_size = len(audio_bytes) - 44
                    duration_seconds = data_size / (sample_rate * channels * (bits_per_sample / 8))
                    info["duration_seconds"] = round(duration_seconds, 2)
                    info["sample_rate"] = sample_rate
                    info["channels"] = channels
            except:
                pass

        return info

    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        return {
            "size_bytes": len(audio_bytes),
            "size_kb": round(len(audio_bytes) / 1024, 2)
        }


def encode_audio_to_base64(audio_bytes: bytes, include_data_url: bool = False, mime_type: str = "audio/wav") -> str:
    """
    Encode audio bytes to base64 string

    Args:
        audio_bytes: Raw audio bytes
        include_data_url: Whether to include data URL prefix
        mime_type: MIME type for data URL

    Returns:
        Base64 encoded string
    """
    base64_str = base64.b64encode(audio_bytes).decode('utf-8')

    if include_data_url:
        return f"data:{mime_type};base64,{base64_str}"

    return base64_str


def validate_and_process_audio(base64_data: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Complete audio validation and processing pipeline

    Args:
        base64_data: Base64 encoded audio

    Returns:
        Tuple of (success, audio_data, error_message)
        audio_data contains: bytes, format, info
    """
    # Decode base64
    success, audio_bytes, error = decode_base64_audio(base64_data)
    if not success:
        return False, None, error

    # Validate format
    is_valid, format_name, error = validate_audio_format(audio_bytes)
    if not is_valid:
        return False, None, error

    # Get info
    info = get_audio_info(audio_bytes)

    return True, {
        "bytes": audio_bytes,
        "format": format_name,
        "info": info
    }, None


def check_audio_duration_estimate(audio_bytes: bytes, max_duration_seconds: int = 300) -> Tuple[bool, Optional[float]]:
    """
    Estimate audio duration and check if within limits

    Args:
        audio_bytes: Raw audio bytes
        max_duration_seconds: Maximum allowed duration

    Returns:
        Tuple of (is_within_limit, estimated_duration)
    """
    info = get_audio_info(audio_bytes)
    duration = info.get("duration_seconds")

    if duration is None:
        # Can't determine duration, assume OK
        logger.warning("Could not determine audio duration")
        return True, None

    is_ok = duration <= max_duration_seconds
    return is_ok, duration
