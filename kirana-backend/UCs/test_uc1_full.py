#!/usr/bin/env python3
"""
Full test for UC1 - Holi Festival Preparation
Sends message and listens on WebSocket for complete response
"""

import asyncio
import json
import httpx
import websockets
from datetime import datetime

async def listen_websocket(store_id, timeout=45):
    """Listen to WebSocket and print events"""
    ws_url = f"ws://localhost:8000/ws/{store_id}"
    step_count = 0

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected! Waiting for messages...\n")

            start_time = asyncio.get_event_loop().time()

            while True:
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - start_time

                if elapsed > timeout:
                    print(f"\n⏱️ Timeout after {timeout}s")
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
                        print(msg_data["data"]["message"])
                        print()
                        print("=" * 80)
                        print(f"✅ Complete! Received {step_count} reasoning steps + final message")
                        print("=" * 80)
                        print()
                        print("🔍 UC1 Verification:")
                        print("   - Should mention Holi festival")
                        print("   - Should recommend gujiya ingredients (besan, khoya, etc.)")
                        print("   - Should recommend gulal/colors")
                        print("   - Should mention coconut powder is ALREADY in stock (5kg)")
                        print("   - Should skip ordering coconut powder")
                        print("=" * 80)
                        # Wait a bit for any trailing events
                        await asyncio.sleep(2)
                        break

                    else:
                        print(f"📨 Event: {event}")
                        print(f"   Data: {json.dumps(msg_data.get('data', {}), indent=2)}")
                        print()

                except asyncio.TimeoutError:
                    print(f"\n⏱️ No more messages")
                    break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

async def test_uc1_with_websocket():
    store_id = "sharma_general_store"

    print("=" * 80)
    print("🔌 Connecting to WebSocket...")
    print("=" * 80)
    print()

    # Start WebSocket listener in background
    ws_task = asyncio.create_task(listen_websocket(store_id, timeout=45))

    # Wait for WebSocket to connect
    await asyncio.sleep(1)

    # Send POST request
    print("=" * 80)
    print("🚀 Sending Holi preparation query to backend...")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/api/message",
            json={
                "store_id": store_id,
                "message_type": "text",
                "content": "Holi aa rahi hai, kya mangana chahiye?",
                "language": "hinglish"
            }
        )

        print(f"✅ Response: {response.status_code}")
        data = response.json()
        print(f"   Message ID: {data['message_id']}")
        print(f"   WebSocket: {data['websocket_channel']}")
        print()

    # Wait for WebSocket to finish
    await ws_task

if __name__ == "__main__":
    print()
    print("=" * 80)
    print("USE CASE 1: Smart Festival Preparation - Holi")
    print("=" * 80)
    print()
    print("Expected behavior:")
    print("  ✅ Detect 'Holi' from Hinglish query")
    print("  ✅ Recommend Holi products (gujiya ingredients + colors + snacks)")
    print("  ✅ Check inventory - coconut powder already has 5kg stock")
    print("  ✅ SKIP coconut powder in recommendation (SMART!)")
    print("  ✅ Show savings from not over-ordering")
    print()
    print("=" * 80)
    print()

    asyncio.run(test_uc1_with_websocket())
