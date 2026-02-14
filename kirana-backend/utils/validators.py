"""
Input validation utilities
Common validation helpers for API inputs
"""

import re
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger


def validate_store_id(store_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate store ID format

    Args:
        store_id: Store identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not store_id or not isinstance(store_id, str):
        return False, "store_id is required and must be a string"

    # Must be alphanumeric with underscores/hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', store_id):
        return False, "store_id must contain only letters, numbers, underscores, and hyphens"

    # Length check (3-50 characters)
    if len(store_id) < 3 or len(store_id) > 50:
        return False, "store_id must be between 3 and 50 characters"

    return True, None


def validate_product_id(product_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate product SKU ID format

    Args:
        product_id: Product SKU identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not product_id or not isinstance(product_id, str):
        return False, "product_id is required and must be a string"

    # Must be alphanumeric with underscores/hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', product_id):
        return False, "product_id must contain only letters, numbers, underscores, and hyphens"

    # Length check (2-100 characters)
    if len(product_id) < 2 or len(product_id) > 100:
        return False, "product_id must be between 2 and 100 characters"

    return True, None


def validate_quantity(quantity: int, allow_negative: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate quantity value

    Args:
        quantity: Quantity to validate
        allow_negative: Whether negative values are allowed

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(quantity, int):
        return False, "quantity must be an integer"

    if not allow_negative and quantity < 0:
        return False, "quantity cannot be negative"

    # Reasonable upper limit
    if abs(quantity) > 100000:
        return False, "quantity exceeds maximum allowed (100,000)"

    return True, None


def validate_price(price: float) -> Tuple[bool, Optional[str]]:
    """
    Validate price value

    Args:
        price: Price to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(price, (int, float)):
        return False, "price must be a number"

    if price < 0:
        return False, "price cannot be negative"

    # Reasonable upper limit (₹1 lakh)
    if price > 100000:
        return False, "price exceeds maximum allowed (₹100,000)"

    return True, None


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Indian phone number

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone or not isinstance(phone, str):
        return False, "phone number is required"

    # Remove common separators
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Check for +91 prefix
    if clean_phone.startswith('+91'):
        clean_phone = clean_phone[3:]
    elif clean_phone.startswith('91') and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]

    # Must be 10 digits
    if not re.match(r'^\d{10}$', clean_phone):
        return False, "phone number must be 10 digits"

    # Must start with 6-9 (Indian mobile numbers)
    if clean_phone[0] not in '6789':
        return False, "phone number must start with 6, 7, 8, or 9"

    return True, None


def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> Tuple[bool, Optional[str]]:
    """
    Validate date string format

    Args:
        date_str: Date string
        format: Expected date format

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str or not isinstance(date_str, str):
        return False, "date is required and must be a string"

    try:
        datetime.strptime(date_str, format)
        return True, None
    except ValueError as e:
        return False, f"Invalid date format. Expected {format}"


def validate_language(language: str) -> Tuple[bool, Optional[str]]:
    """
    Validate language code

    Args:
        language: Language code

    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_languages = {"hinglish", "hindi", "english", "kannada", "tamil", "telugu", "marathi"}

    if not language or not isinstance(language, str):
        return False, "language is required"

    language_lower = language.lower()

    if language_lower not in supported_languages:
        return False, f"Unsupported language. Supported: {', '.join(supported_languages)}"

    return True, None


def validate_transaction_type(transaction_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate transaction type

    Args:
        transaction_type: Transaction type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = {"cash", "upi", "credit", "supplier_delivery"}

    if not transaction_type or not isinstance(transaction_type, str):
        return False, "transaction_type is required"

    if transaction_type.lower() not in valid_types:
        return False, f"Invalid transaction type. Valid: {', '.join(valid_types)}"

    return True, None


def validate_customer_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate customer name

    Args:
        name: Customer name

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "customer name is required"

    # Remove extra whitespace
    name_clean = name.strip()

    # Minimum length
    if len(name_clean) < 2:
        return False, "customer name must be at least 2 characters"

    # Maximum length
    if len(name_clean) > 100:
        return False, "customer name too long (max 100 characters)"

    # Allow letters, spaces, and common Indian name characters
    if not re.match(r'^[a-zA-Z\s\.\-\']+$', name_clean):
        return False, "customer name contains invalid characters"

    return True, None


def validate_upi_id(upi_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate UPI ID format

    Args:
        upi_id: UPI ID string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not upi_id or not isinstance(upi_id, str):
        return False, "UPI ID is required"

    # Basic UPI format: username@provider
    if "@" not in upi_id:
        return False, "UPI ID must contain @"

    parts = upi_id.split("@")
    if len(parts) != 2:
        return False, "Invalid UPI ID format"

    username, provider = parts

    # Username validation (alphanumeric, dots, underscores)
    if not re.match(r'^[a-zA-Z0-9\._-]{3,}$', username):
        return False, "Invalid UPI username (min 3 characters, alphanumeric with . _ -)"

    # Provider validation
    if not re.match(r'^[a-zA-Z0-9\.]+$', provider):
        return False, "Invalid UPI provider"

    return True, None


def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input (remove harmful characters, trim)

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Trim whitespace
    sanitized = sanitized.strip()

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
