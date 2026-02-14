"""
Test script for API endpoints
Tests all routes with httpx
"""

import httpx
import asyncio
from datetime import datetime


BASE_URL = "http://localhost:8000"
STORE_ID = "sharma_general_store"


async def test_health_endpoints():
    """Test health check endpoints"""
    print("Testing Health Endpoints...")

    async with httpx.AsyncClient() as client:
        # Test root endpoint
        response = await client.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"  ✅ GET / - {data['message']}")

        # Test health endpoint
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["gemini_api_configured"] == True
        print(f"  ✅ GET /health - Gemini: {data['gemini_api_configured']}, Weather: {data['weather_api_configured']}")


async def test_store_endpoints():
    """Test store data endpoints"""
    print("\nTesting Store Endpoints...")

    async with httpx.AsyncClient() as client:
        # Test get profile
        response = await client.get(f"{BASE_URL}/api/store/{STORE_ID}/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["store_id"] == STORE_ID
        print(f"  ✅ GET /api/store/{STORE_ID}/profile - {data['store_name']}")

        # Test get inventory
        response = await client.get(f"{BASE_URL}/api/store/{STORE_ID}/inventory")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "alerts" in data
        print(f"  ✅ GET /api/store/{STORE_ID}/inventory - {data['total_products']} products, {data['low_stock_count']} low stock")

        # Test get P&L
        response = await client.get(f"{BASE_URL}/api/store/{STORE_ID}/pnl")
        assert response.status_code == 200
        data = response.json()
        assert "daily_summary" in data
        summary = data["daily_summary"]
        print(f"  ✅ GET /api/store/{STORE_ID}/pnl - ₹{summary['total_revenue']:.2f} revenue, {summary['items_sold']} items sold")

        # Test get forecast
        response = await client.get(f"{BASE_URL}/api/store/{STORE_ID}/forecast?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "forecasts" in data
        assert data["forecast_days"] == 7
        print(f"  ✅ GET /api/store/{STORE_ID}/forecast - {len(data['forecasts'])} product forecasts generated")


async def test_message_endpoint():
    """Test message processing endpoint"""
    print("\nTesting Message Endpoint...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test text message
        message_data = {
            "store_id": STORE_ID,
            "message_type": "text",
            "content": "Maggi ka stock kitna hai?",
            "language": "hinglish"
        }

        response = await client.post(f"{BASE_URL}/api/message", json=message_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "message_id" in data
        assert "websocket_channel" in data
        print(f"  ✅ POST /api/message (text) - Message ID: {data['message_id']}")
        print(f"     WebSocket: {data['websocket_channel']}")


async def test_error_handling():
    """Test error handling"""
    print("\nTesting Error Handling...")

    async with httpx.AsyncClient() as client:
        # Test invalid store_id
        response = await client.get(f"{BASE_URL}/api/store/invalid/profile")
        # Could be 400 (validation) or 404 (not found)
        assert response.status_code in [400, 404]
        print(f"  ✅ Invalid store_id rejected ({response.status_code})")

        # Test non-existent store
        response = await client.get(f"{BASE_URL}/api/store/non_existent_store/profile")
        # Could be 400 (validation) or 404 (not found)
        assert response.status_code in [400, 404]
        print(f"  ✅ Non-existent store handled ({response.status_code})")

        # Test invalid message
        invalid_message = {
            "store_id": STORE_ID,
            "message_type": "text",
            "content": ""  # Empty content
        }
        response = await client.post(f"{BASE_URL}/api/message", json=invalid_message)
        assert response.status_code == 400
        print(f"  ✅ Invalid message rejected (400)")


async def main():
    print("=" * 60)
    print("KiranaGPT Backend - API Endpoint Testing")
    print("=" * 60)
    print()
    print("⚠️  Make sure the server is running on http://localhost:8000")
    print()

    try:
        # Test if server is running
        async with httpx.AsyncClient() as client:
            try:
                await client.get(f"{BASE_URL}/", timeout=2.0)
            except httpx.ConnectError:
                print("❌ Server not running. Please start the server first:")
                print("   python main.py")
                return 1

        # Run tests
        await test_health_endpoints()
        await test_store_endpoints()
        await test_message_endpoint()
        await test_error_handling()

        print()
        print("=" * 60)
        print("✅ All API endpoint tests passed!")
        print("=" * 60)
        print()
        print("API Summary:")
        print("  • Health Endpoints: GET / and GET /health ✅")
        print("  • Store Profile: GET /api/store/{id}/profile ✅")
        print("  • Inventory: GET /api/store/{id}/inventory ✅")
        print("  • P&L: GET /api/store/{id}/pnl ✅")
        print("  • Forecast: GET /api/store/{id}/forecast ✅")
        print("  • Message: POST /api/message ✅")
        print("  • WebSocket: WS /ws/{store_id} (ready)")
        print()
        print("📚 API Documentation: http://localhost:8000/docs")
        return 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ API test failed: Assertion error")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ API test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
