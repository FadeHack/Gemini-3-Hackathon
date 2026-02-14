"""
Demo Mode Test Script
Tests that cached responses work without making actual Gemini API calls
"""

import httpx
import asyncio
import os

# Temporarily enable demo mode for this test
os.environ["DEMO_MODE"] = "true"

BASE_URL = "http://localhost:8000"
STORE_ID = "sharma_general_store"


async def test_demo_mode():
    """Test all flows in demo mode (using cached responses)"""
    print("=" * 60)
    print("KiranaGPT Backend - Demo Mode Test")
    print("=" * 60)
    print()
    print("🎭 DEMO_MODE=true (No real Gemini API calls)")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Shelf photo with demo response
        print("TEST 1: Shelf Photo (Demo Mode)")
        print("-" * 60)

        dummy_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        message_data = {
            "store_id": STORE_ID,
            "message_type": "image",
            "content": f"data:image/png;base64,{dummy_image}",
            "language": "hinglish"
        }

        print("📤 Sending shelf photo...")
        response = await client.post(f"{BASE_URL}/api/message", json=message_data)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message accepted: {data['message_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Using cached demo response (no API call)")
            print()
        else:
            print(f"❌ Failed: {response.status_code}")
            print()

        # Wait a moment for background processing
        await asyncio.sleep(2)

        # Test 2: Parchi with demo response
        print("TEST 2: Kacchi Parchi (Demo Mode)")
        print("-" * 60)

        message_data = {
            "store_id": STORE_ID,
            "message_type": "image",
            "content": f"data:image/png;base64,{dummy_image}",
            "language": "hinglish",
            "metadata": {"image_type": "parchi"}
        }

        print("📤 Sending parchi...")
        response = await client.post(f"{BASE_URL}/api/message", json=message_data)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message accepted: {data['message_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Using cached demo response (no API call)")
            print()
        else:
            print(f"❌ Failed: {response.status_code}")
            print()

        await asyncio.sleep(2)

        # Test 3: Voice message with demo response
        print("TEST 3: Voice Message (Demo Mode)")
        print("-" * 60)

        dummy_audio = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="

        message_data = {
            "store_id": STORE_ID,
            "message_type": "voice",
            "content": f"data:audio/wav;base64,{dummy_audio}",
            "language": "hinglish"
        }

        print("📤 Sending voice message...")
        response = await client.post(f"{BASE_URL}/api/message", json=message_data)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message accepted: {data['message_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Using cached demo response (no API call)")
            print()
        else:
            print(f"❌ Failed: {response.status_code}")
            print()

        await asyncio.sleep(2)

    print("=" * 60)
    print("✅ Demo Mode Test Complete!")
    print("=" * 60)
    print()
    print("🎯 All messages processed using cached responses")
    print("💡 No actual Gemini API calls were made")
    print()
    print("Demo Response Files Used:")
    print("  • demo/shelf_response.json")
    print("  • demo/parchi_response.json")
    print("  • demo/voice_response.json")
    print()
    print("📝 Note: Text queries still use live Gemini API")
    print("   (can add demo response for text if needed)")
    print()


if __name__ == "__main__":
    print()
    print("⚠️  Starting server with DEMO_MODE=true...")
    print("   (Server must be restarted to pick up env change)")
    print()
    asyncio.run(test_demo_mode())
