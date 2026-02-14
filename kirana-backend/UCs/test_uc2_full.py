#!/usr/bin/env python3
"""
Full test for UC2 - Sends message and listens on WebSocket for complete response
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime

async def test_uc2_with_websocket():
    store_id = "sharma_general_store"

    # Step 1: Send POST request
    print("=" * 80)
    print("🚀 Sending message to backend...")
    print("=" * 80)

    response = requests.post(
        "http://localhost:8000/api/message",
        json={
            "store_id": store_id,
            "message_type": "text",
            "content": "Kya order karein aaj?",
            "language": "hinglish"
        }
    )

    print(f"✅ Response: {response.status_code}")
    data = response.json()
    print(f"   Message ID: {data['message_id']}")
    print(f"   WebSocket: {data['websocket_channel']}")
    print()

    # Step 2: Connect to WebSocket and listen
    ws_url = f"ws://localhost:8000/ws/{store_id}"
    print("=" * 80)
    print(f"🔌 Connecting to WebSocket: {ws_url}")
    print("=" * 80)
    print()

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected! Waiting for messages...\n")

            # Listen for messages (with timeout)
            step_count = 0
            timeout = 30  # 30 seconds timeout

            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                    msg_data = json.loads(message)

                    event = msg_data.get("event", msg_data.get("event_type"))

                    if event == "reasoning_step":
                        step_count += 1
                        step = msg_data["data"]
                        step_num = step.get('step_number', step_count)
                        print(f"📊 Step {step_num}: {step.get('icon', '💡')} {step.get('title', 'Processing...')}")
                        print(f"   → {step.get('description', '')}")
                        if step.get('details'):
                            print(f"   Details: {json.dumps(step['details'], indent=6)}")
                        print()

                    elif event == "chat_message":
                        print("=" * 80)
                        print("💬 FINAL RESPONSE:")
                        print("=" * 80)
                        print(msg_data["data"]["message"])
                        print()
                        print("=" * 80)
                        print(f"✅ Complete! Received {step_count} reasoning steps + final message")
                        print("=" * 80)
                        break

                    else:
                        print(f"📨 Event: {event}")
                        print(f"   Data: {json.dumps(msg_data.get('data', {}), indent=2)}")
                        print()

            except asyncio.TimeoutError:
                print(f"\n⏱️ Timeout after {timeout}s - no more messages")
                print(f"Received {step_count} reasoning steps")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_uc2_with_websocket())
