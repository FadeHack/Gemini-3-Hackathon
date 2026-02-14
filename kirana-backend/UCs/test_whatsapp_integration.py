#!/usr/bin/env python3
"""
Test WhatsApp integration flow
Tests the complete flow from sending a message via HTTP POST to receiving WebSocket updates
Similar to UC1/UC2 but focused on diagnosing WhatsApp integration
"""

import asyncio
import json
import httpx
import websockets
from datetime import datetime


async def listen_websocket(store_id, timeout=30):
    """Listen to WebSocket and print events"""
    ws_url = f"ws://localhost:8000/ws/{store_id}"
    step_count = 0

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected! Listening for events...\n")

            start_time = asyncio.get_event_loop().time()

            while True:
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time

                if elapsed > timeout:
                    print(f"\n⏱️  Timeout after {timeout}s")
                    break

                try:
                    remaining_timeout = timeout - elapsed
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=remaining_timeout
                    )

                    msg_data = json.loads(message)
                    event = msg_data.get("event", msg_data.get("event_type"))

                    if event == "connection_established":
                        print(f"📨 {event}")
                        print(f"   Data: {msg_data.get('data', {})}")
                        print()

                    elif event == "reasoning_step":
                        step_count += 1
                        step = msg_data["data"]
                        step_num = step.get('step_number', step_count)
                        print(f"📊 Step {step_num}: {step.get('icon', '💡')} {step.get('step_type', 'Processing...')}")
                        print(f"   → {step.get('description', '')}")
                        if step.get('details'):
                            print(f"   Details: {json.dumps(step['details'], indent=6)}")
                        print()

                    elif event == "chat_message":
                        print("=" * 80)
                        print("💬 FINAL AI RESPONSE:")
                        print("=" * 80)
                        print(msg_data["data"]["content"])
                        print()
                        print("=" * 80)
                        print(f"✅ Complete! Received {step_count} reasoning steps + final message")
                        print("=" * 80)
                        # Wait a bit for any trailing events
                        await asyncio.sleep(2)
                        break

                    else:
                        print(f"📨 Event: {event}")
                        print(f"   Data: {json.dumps(msg_data.get('data', {}), indent=2)}")
                        print()

                except asyncio.TimeoutError:
                    print(f"\n⏱️  No more messages")
                    break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()


async def test_whatsapp_flow():
    """Test the WhatsApp message flow"""
    store_id = "sharma_general_store"

    print("=" * 80)
    print("🧪 TESTING WHATSAPP INTEGRATION")
    print("=" * 80)
    print()
    print("This test simulates the flow when a user sends a WhatsApp message:")
    print("  1. Connect to WebSocket (ws://localhost:8000/ws/{store_id})")
    print("  2. Send HTTP POST to /api/message")
    print("  3. Listen for WebSocket events (reasoning steps + final response)")
    print()
    print("=" * 80)
    print()

    # Step 1: Connect to WebSocket FIRST
    print("🔌 Step 1: Connecting to WebSocket...")
    print("=" * 80)
    print()

    # Start WebSocket listener in background
    ws_task = asyncio.create_task(listen_websocket(store_id, timeout=30))

    # Wait for WebSocket to connect
    await asyncio.sleep(1)

    # Step 2: Send HTTP POST request
    print("=" * 80)
    print("📤 Step 2: Sending message via HTTP POST...")
    print("=" * 80)

    test_message = {
        "store_id": store_id,
        "message_type": "text",
        "content": "Maggi ka stock kitna hai?",
        "language": "hinglish"
    }

    print(f"Request body: {json.dumps(test_message, indent=2)}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/message",
                json=test_message
            )

            print(f"✅ Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   Message ID: {data.get('message_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   WebSocket channel: {data.get('websocket_channel')}")
                print()
            else:
                print(f"❌ Error response: {response.text}")
                print()

        except Exception as e:
            print(f"❌ HTTP request failed: {e}")
            import traceback
            traceback.print_exc()
            return

    # Step 3: Wait for WebSocket to finish receiving messages
    print("=" * 80)
    print("👂 Step 3: Listening for WebSocket updates...")
    print("=" * 80)
    print()

    await ws_task


async def main():
    print()
    print("=" * 80)
    print("WHATSAPP INTEGRATION DIAGNOSTIC TEST")
    print("=" * 80)
    print()
    print("Prerequisites:")
    print("  ✓ Backend running on http://localhost:8000")
    print("  ✓ Store data loaded for 'sharma_general_store'")
    print()
    print("Expected flow:")
    print("  1. WebSocket connection established")
    print("  2. HTTP POST returns 200 with message_id")
    print("  3. WebSocket receives reasoning_step events")
    print("  4. WebSocket receives final chat_message event")
    print()
    print("=" * 80)
    print()

    await test_whatsapp_flow()

    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
