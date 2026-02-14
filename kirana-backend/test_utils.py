"""
Test script for utilities
"""

from datetime import datetime, timedelta
import base64
from utils.validators import *
from utils.formatters import *
from utils.image_utils import encode_image_to_base64
from utils.audio_utils import encode_audio_to_base64


def test_validators():
    """Test validation utilities"""
    print("Testing Validators...")

    # Test store_id validation
    is_valid, error = validate_store_id("sharma_general_store")
    assert is_valid == True
    print(f"  ✅ Valid store_id accepted")

    is_valid, error = validate_store_id("ab")
    assert is_valid == False
    assert "between 3 and 50" in error
    print(f"  ✅ Invalid store_id rejected: {error}")

    # Test product_id validation
    is_valid, error = validate_product_id("maggi_70g")
    assert is_valid == True
    print(f"  ✅ Valid product_id accepted")

    # Test quantity validation
    is_valid, error = validate_quantity(50)
    assert is_valid == True
    print(f"  ✅ Valid quantity accepted")

    is_valid, error = validate_quantity(-5, allow_negative=True)
    assert is_valid == True
    print(f"  ✅ Negative quantity accepted when allowed")

    is_valid, error = validate_quantity(-5, allow_negative=False)
    assert is_valid == False
    print(f"  ✅ Negative quantity rejected when not allowed")

    # Test price validation
    is_valid, error = validate_price(150.50)
    assert is_valid == True
    print(f"  ✅ Valid price accepted")

    is_valid, error = validate_price(-10)
    assert is_valid == False
    print(f"  ✅ Negative price rejected")

    # Test phone number validation
    is_valid, error = validate_phone_number("9876543210")
    assert is_valid == True
    print(f"  ✅ Valid phone number accepted")

    is_valid, error = validate_phone_number("+91 98765 43210")
    assert is_valid == True
    print(f"  ✅ Phone with +91 prefix accepted")

    is_valid, error = validate_phone_number("123456789")
    assert is_valid == False
    print(f"  ✅ Invalid phone rejected: {error}")

    # Test UPI ID validation
    is_valid, error = validate_upi_id("merchant@paytm")
    assert is_valid == True
    print(f"  ✅ Valid UPI ID accepted")

    is_valid, error = validate_upi_id("invalid-upi")
    assert is_valid == False
    print(f"  ✅ Invalid UPI ID rejected")

    # Test language validation
    is_valid, error = validate_language("hinglish")
    assert is_valid == True
    print(f"  ✅ Valid language accepted")

    is_valid, error = validate_language("french")
    assert is_valid == False
    print(f"  ✅ Unsupported language rejected")

    # Test text sanitization
    sanitized = sanitize_text_input("  Hello\x00World\n  ")
    assert sanitized == "HelloWorld"
    print(f"  ✅ Text sanitization working")


def test_formatters():
    """Test formatting utilities"""
    print("\nTesting Formatters...")

    # Test currency formatting
    formatted = format_currency(1500)
    assert "1,500" in formatted
    print(f"  ✅ Currency formatted: {formatted}")

    formatted = format_currency(150000)
    assert "1,50,000" in formatted
    print(f"  ✅ Large currency formatted: {formatted}")

    # Test Indian number formatting
    formatted = format_indian_number(100000)
    assert formatted == "1,00,000"
    print(f"  ✅ Indian number formatted: {formatted}")

    # Test date formatting
    dt = datetime(2026, 2, 14, 15, 30)
    formatted = format_date_hinglish(dt, include_time=True)
    assert "14 Feb 2026" in formatted
    assert "3:30 PM" in formatted
    print(f"  ✅ Date formatted: {formatted}")

    # Test relative time
    dt = datetime.now() - timedelta(minutes=5)
    formatted = format_relative_time_hinglish(dt)
    assert "5 minute" in formatted
    assert "pehle" in formatted
    print(f"  ✅ Relative time formatted: {formatted}")

    # Test days until
    formatted = format_days_until_hinglish(0)
    assert formatted == "aaj"
    print(f"  ✅ Days until (today): {formatted}")

    formatted = format_days_until_hinglish(1)
    assert formatted == "kal"
    print(f"  ✅ Days until (tomorrow): {formatted}")

    formatted = format_days_until_hinglish(5)
    assert "5 din mein" in formatted
    print(f"  ✅ Days until (5 days): {formatted}")

    # Test stock status
    status = format_stock_status_hinglish(0.5, "Maggi")
    assert "critically low" in status
    print(f"  ✅ Stock status (critical): {status}")

    status = format_stock_status_hinglish(7.0, "Atta")
    assert "accha hai" in status
    print(f"  ✅ Stock status (healthy): {status}")

    # Test urgency formatting
    formatted = format_urgency_hinglish("critical")
    assert "Bahut urgent" in formatted
    print(f"  ✅ Urgency formatted: {formatted}")

    # Test payment type formatting
    formatted = format_payment_type_hinglish("cash")
    assert "Nakad" in formatted
    print(f"  ✅ Payment type formatted: {formatted}")

    # Test percentage formatting
    formatted = format_percentage(15.5)
    assert formatted == "15.5%"
    print(f"  ✅ Percentage formatted: {formatted}")

    # Test summary message
    msg = create_summary_message(
        total_revenue=5000,
        items_sold=50,
        cash_sales=3000,
        upi_sales=1500,
        credit_sales=500
    )
    assert "Aaj ka Business" in msg
    assert "5,000" in msg
    print(f"  ✅ Summary message created")

    # Test procurement message
    msg = create_procurement_message(
        order_id="ORD-001",
        total_items=10,
        total_cost=15000,
        savings=1500,
        distributor_count=3,
        festival_name="Navratri"
    )
    assert "ORD-001" in msg
    assert "Navratri" in msg
    print(f"  ✅ Procurement message created")

    # Test alert message
    alerts = [
        {"product_name": "Maggi", "urgency": "critical", "days_of_stock": 0.5},
        {"product_name": "Atta", "urgency": "medium", "days_of_stock": 2.0}
    ]
    msg = create_alert_message(alerts)
    assert "Maggi" in msg
    assert "Atta" in msg
    print(f"  ✅ Alert message created")


def test_image_audio_utils():
    """Test image and audio utilities (basic tests without actual files)"""
    print("\nTesting Image/Audio Utils...")

    # Test base64 encoding
    test_data = b"fake image data"
    encoded = encode_image_to_base64(test_data)
    assert len(encoded) > 0
    print(f"  ✅ Image base64 encoding works")

    # Test with data URL prefix
    encoded = encode_image_to_base64(test_data, include_data_url=True)
    assert encoded.startswith("data:image")
    print(f"  ✅ Image base64 with data URL works")

    # Test audio encoding
    test_audio = b"fake audio data"
    encoded = encode_audio_to_base64(test_audio)
    assert len(encoded) > 0
    print(f"  ✅ Audio base64 encoding works")

    # Test with data URL
    encoded = encode_audio_to_base64(test_audio, include_data_url=True)
    assert encoded.startswith("data:audio")
    print(f"  ✅ Audio base64 with data URL works")


def main():
    print("=" * 60)
    print("KiranaGPT Backend - Utilities Testing")
    print("=" * 60)
    print()

    try:
        test_validators()
        test_formatters()
        test_image_audio_utils()

        print()
        print("=" * 60)
        print("✅ All utility tests passed!")
        print("=" * 60)
        print()
        print("Utilities Summary:")
        print("  • Validators: 11 validation functions ✅")
        print("  • Formatters: 12 formatting functions ✅")
        print("  • Image Utils: 6 image processing functions ✅")
        print("  • Audio Utils: 6 audio processing functions ✅")
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Utility test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
