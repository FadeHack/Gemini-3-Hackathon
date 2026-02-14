"""
Utilities package
Helper functions for image/audio processing, validation, and formatting
"""

from .image_utils import (
    decode_base64_image,
    validate_image_format,
    get_image_info,
    resize_image_if_needed,
    encode_image_to_base64,
    validate_and_process_image
)

from .audio_utils import (
    decode_base64_audio,
    validate_audio_format,
    get_audio_info,
    encode_audio_to_base64,
    validate_and_process_audio,
    check_audio_duration_estimate
)

from .validators import (
    validate_store_id,
    validate_product_id,
    validate_quantity,
    validate_price,
    validate_phone_number,
    validate_date_string,
    validate_language,
    validate_transaction_type,
    validate_customer_name,
    validate_upi_id,
    sanitize_text_input
)

from .formatters import (
    format_currency,
    format_indian_number,
    format_date_hinglish,
    format_relative_time_hinglish,
    format_days_until_hinglish,
    format_stock_status_hinglish,
    format_urgency_hinglish,
    format_payment_type_hinglish,
    format_percentage,
    create_summary_message,
    create_procurement_message,
    create_alert_message
)

__all__ = [
    # Image utils
    "decode_base64_image",
    "validate_image_format",
    "get_image_info",
    "resize_image_if_needed",
    "encode_image_to_base64",
    "validate_and_process_image",
    # Audio utils
    "decode_base64_audio",
    "validate_audio_format",
    "get_audio_info",
    "encode_audio_to_base64",
    "validate_and_process_audio",
    "check_audio_duration_estimate",
    # Validators
    "validate_store_id",
    "validate_product_id",
    "validate_quantity",
    "validate_price",
    "validate_phone_number",
    "validate_date_string",
    "validate_language",
    "validate_transaction_type",
    "validate_customer_name",
    "validate_upi_id",
    "sanitize_text_input",
    # Formatters
    "format_currency",
    "format_indian_number",
    "format_date_hinglish",
    "format_relative_time_hinglish",
    "format_days_until_hinglish",
    "format_stock_status_hinglish",
    "format_urgency_hinglish",
    "format_payment_type_hinglish",
    "format_percentage",
    "create_summary_message",
    "create_procurement_message",
    "create_alert_message",
]
