"""
Test script for services
"""

import asyncio
import json
from datetime import datetime
from services.gemini_service import get_gemini_service
from services.websocket_service import get_websocket_manager
from services.message_service import get_message_router
from services.weather_service import get_weather_service
from services.upi_service import (
    generate_upi_deeplink,
    validate_upi_id,
    parse_upi_deeplink
)
from models.message import MessageInput
from config.constants import MessageType


def test_message_router():
    """Test message routing service"""
    print("Testing MessageRouter...")

    router = get_message_router()

    # Test text message detection
    text_msg = MessageInput(
        store_id="sharma_general_store",
        message_type="text",
        content="Maggi ka stock kitna hai?"
    )

    msg_type = router.detect_message_type(text_msg)
    assert msg_type == MessageType.TEXT
    print(f"  ✅ Text message detected: {msg_type}")

    # Test image message detection
    image_msg = MessageInput(
        store_id="sharma_general_store",
        message_type="image",
        content="base64encodedimagedata=="
    )

    msg_type = router.detect_message_type(image_msg)
    assert msg_type == MessageType.IMAGE
    print(f"  ✅ Image message detected: {msg_type}")

    # Test voice message detection
    voice_msg = MessageInput(
        store_id="sharma_general_store",
        message_type="voice",
        content="base64encodedaudiodata=="
    )

    msg_type = router.detect_message_type(voice_msg)
    assert msg_type == MessageType.VOICE
    print(f"  ✅ Voice message detected: {msg_type}")


async def test_weather_service():
    """Test weather service"""
    print("\nTesting WeatherService...")

    service = get_weather_service()

    # Test current weather
    weather = await service.get_current_weather("Indore", "IN")
    assert "temp_c" in weather
    assert "condition" in weather
    assert "city" in weather
    print(f"  ✅ Current weather for {weather['city']}: {weather['temp_c']}°C, {weather['condition']}")

    # Test forecast
    forecast = await service.get_forecast("Mumbai", "IN", days=3)
    assert len(forecast) > 0
    assert len(forecast) <= 3
    print(f"  ✅ Forecast retrieved: {len(forecast)} days")
    if forecast:
        print(f"     Tomorrow: {forecast[0]['temp_avg']}°C, {forecast[0]['condition']}")


def test_upi_service():
    """Test UPI service"""
    print("\nTesting UPI Service...")

    # Test UPI ID validation
    valid_upi = "merchant@paytm"
    assert validate_upi_id(valid_upi) == True
    print(f"  ✅ Valid UPI ID accepted: {valid_upi}")

    invalid_upi = "invalid-upi"
    assert validate_upi_id(invalid_upi) == False
    print(f"  ✅ Invalid UPI ID rejected: {invalid_upi}")

    # Test deeplink generation
    deeplink = generate_upi_deeplink(
        upi_id="patelwholesale@paytm",
        name="Patel Wholesale",
        amount=15420.50,
        transaction_note="Order #ORD-001",
        transaction_ref="ORD-001"
    )
    assert deeplink.startswith("upi://pay?")
    assert "pa=patelwholesale" in deeplink
    assert "am=15420.50" in deeplink
    print(f"  ✅ UPI deeplink generated")
    print(f"     {deeplink[:80]}...")

    # Test deeplink parsing
    parsed = parse_upi_deeplink(deeplink)
    assert parsed["upi_id"] == "patelwholesale@paytm"
    assert parsed["amount"] == 15420.50
    assert parsed["transaction_ref"] == "ORD-001"
    print(f"  ✅ Deeplink parsed: ₹{parsed['amount']}, ref={parsed['transaction_ref']}")


def test_websocket_manager():
    """Test WebSocket manager"""
    print("\nTesting WebSocketManager...")

    manager = get_websocket_manager()

    # Test connection count
    count = manager.get_total_connections()
    assert count >= 0
    print(f"  ✅ WebSocketManager initialized, {count} active connections")

    # Test store-specific count
    store_count = manager.get_connection_count("sharma_general_store")
    assert store_count >= 0
    print(f"  ✅ Store connection count: {store_count}")


async def test_gemini_service():
    """Test Gemini service with real API call"""
    print("\nTesting GeminiService...")

    service = get_gemini_service()
    print(f"  ✅ GeminiService initialized with model={service.model_name}")
    print(f"     Demo mode: {service.demo_mode}")

    # Test text query with real API call
    if service.demo_mode:
        print("  ⚠️  Running in demo mode (no actual API calls)")
    else:
        print("  ℹ️  Testing with live Gemini API...")

        try:
            store_context = {
                "store_name": "Sharma General Store",
                "owner_name": "Rajesh",
                "city": "Indore",
                "language": "hinglish"
            }
            response = await service.process_text_query(
                "What is KiranaGPT?",
                store_context
            )
            print(f"  ✅ Text query processed successfully")
            print(f"     Response: {response.message_to_owner[:150]}...")
            print(f"     Response type: {response.response_type}")
        except Exception as e:
            print(f"  ❌ API call failed: {e}")
            raise


async def main():
    print("=" * 60)
    print("KiranaGPT Backend - Services Testing")
    print("=" * 60)
    print()

    try:
        # Test sync services
        test_message_router()
        test_upi_service()
        test_websocket_manager()

        # Test async services
        await test_weather_service()
        await test_gemini_service()

        print()
        print("=" * 60)
        print("✅ All service tests passed!")
        print("=" * 60)
        print()
        print("Services Summary:")
        print("  • GeminiService: Initialized ✅")
        print("  • WebSocketManager: Ready ✅")
        print("  • MessageRouter: Validated ✅")
        print("  • WeatherService: Fetching data ✅")
        print("  • UPI Service: Generating deeplinks ✅")
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Service test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
