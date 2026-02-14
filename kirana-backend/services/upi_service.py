"""
UPI payment deep link service
Generates UPI payment URLs for procurement orders and customer payments
"""

from typing import Optional
from urllib.parse import urlencode
from loguru import logger

from config.constants import UPI_CONFIG


def generate_upi_deeplink(
    upi_id: str,
    name: str,
    amount: float,
    transaction_note: Optional[str] = None,
    transaction_ref: Optional[str] = None
) -> str:
    """
    Generate UPI payment deep link

    Args:
        upi_id: Payee's UPI ID (e.g., "merchant@paytm")
        name: Payee's name
        amount: Payment amount in INR
        transaction_note: Optional transaction note
        transaction_ref: Optional transaction reference/ID

    Returns:
        UPI deep link string (upi://pay?...)

    Example:
        >>> generate_upi_deeplink(
        ...     upi_id="merchant@paytm",
        ...     name="Patel Wholesale",
        ...     amount=15420.50,
        ...     transaction_note="Order #ORD-20260214-001",
        ...     transaction_ref="ORD-20260214-001"
        ... )
        'upi://pay?pa=merchant@paytm&pn=Patel%20Wholesale&am=15420.50&...'
    """
    try:
        # Build UPI parameters
        params = {
            "pa": upi_id,  # Payee address (UPI ID)
            "pn": name,    # Payee name
            "am": f"{amount:.2f}",  # Amount (2 decimal places)
            "cu": "INR",   # Currency
        }

        # Add optional parameters
        if transaction_note:
            params["tn"] = transaction_note  # Transaction note

        if transaction_ref:
            params["tr"] = transaction_ref  # Transaction reference

        # Generate deep link
        base_url = UPI_CONFIG["base_url"]
        deeplink = f"{base_url}?{urlencode(params)}"

        logger.debug(
            f"Generated UPI deeplink for {name}: ₹{amount:.2f}, "
            f"ref={transaction_ref}"
        )

        return deeplink

    except Exception as e:
        logger.error(f"Error generating UPI deeplink: {e}")
        raise


def validate_upi_id(upi_id: str) -> bool:
    """
    Validate UPI ID format

    Args:
        upi_id: UPI ID to validate

    Returns:
        True if valid format

    Example:
        >>> validate_upi_id("merchant@paytm")
        True
        >>> validate_upi_id("invalid-upi")
        False
    """
    try:
        # UPI ID format: username@provider
        if "@" not in upi_id:
            return False

        username, provider = upi_id.split("@", 1)

        # Username should be alphanumeric + some special chars
        if not username or len(username) < 3:
            return False

        # Provider should exist
        if not provider:
            return False

        # Common UPI providers (not exhaustive)
        valid_providers = [
            "paytm", "googlepay", "phonepe", "amazonpay", "ybl",
            "okaxis", "okicici", "okhdfcbank", "oksbi", "axisbank",
            "icici", "hdfcbank", "sbi", "upi"
        ]

        # Accept any provider ending with known ones or just check format
        if provider.lower() not in valid_providers and not any(
            provider.lower().endswith(vp) for vp in valid_providers
        ):
            # Still accept if it looks like a valid domain
            if "." not in provider:
                logger.warning(f"Unusual UPI provider: {provider}")

        return True

    except Exception as e:
        logger.error(f"Error validating UPI ID {upi_id}: {e}")
        return False


def parse_upi_deeplink(deeplink: str) -> dict:
    """
    Parse UPI deep link into components

    Args:
        deeplink: UPI deep link string

    Returns:
        Dict with parsed components

    Example:
        >>> parse_upi_deeplink("upi://pay?pa=test@paytm&pn=Test&am=100.00")
        {'upi_id': 'test@paytm', 'name': 'Test', 'amount': 100.0, ...}
    """
    from urllib.parse import urlparse, parse_qs

    try:
        parsed = urlparse(deeplink)

        if parsed.scheme != "upi":
            raise ValueError("Not a valid UPI deep link")

        # Parse query parameters
        params = parse_qs(parsed.query)

        # Extract values (parse_qs returns lists)
        result = {
            "upi_id": params.get("pa", [None])[0],
            "name": params.get("pn", [None])[0],
            "amount": float(params.get("am", [0])[0]) if params.get("am") else None,
            "currency": params.get("cu", ["INR"])[0],
            "transaction_note": params.get("tn", [None])[0],
            "transaction_ref": params.get("tr", [None])[0],
        }

        return result

    except Exception as e:
        logger.error(f"Error parsing UPI deeplink: {e}")
        raise


def format_upi_qr_data(deeplink: str) -> str:
    """
    Format UPI deep link for QR code generation

    Args:
        deeplink: UPI deep link

    Returns:
        QR code data string (same as deeplink for UPI)
    """
    # For UPI, QR code data is the same as the deep link
    # QR code libraries will encode this as-is
    return deeplink
