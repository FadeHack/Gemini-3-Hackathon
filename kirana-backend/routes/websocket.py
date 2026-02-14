"""
WebSocket routes
Real-time bidirectional communication for streaming AI responses
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from services.websocket_service import get_websocket_manager
from utils.validators import validate_store_id

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{store_id}")
async def websocket_endpoint(websocket: WebSocket, store_id: str):
    """
    WebSocket endpoint for real-time updates

    Establishes a WebSocket connection for streaming AI reasoning steps,
    chat messages, inventory updates, and procurement orders in real-time.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Event Types Sent:**
    - `connection_established`: Confirmation of connection
    - `reasoning_step`: AI reasoning step updates
    - `chat_message`: Chat responses
    - `inventory_update`: Stock level changes
    - `procurement_order`: Generated orders
    - `error`: Error notifications

    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/sharma_general_store');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(`Event: ${data.event_type}`, data);
    };
    ```

    **Event Format:**
    ```json
    {
      "event_type": "reasoning_step",
      "timestamp": "2026-02-14T14:30:00Z",
      "step_type": "SHELF_ANALYSIS",
      "description": "Analyzing shelf photo...",
      "details": {...},
      "icon": "🔍"
    }
    ```
    """
    ws_manager = get_websocket_manager()

    # Validate store_id
    is_valid, error = validate_store_id(store_id)
    if not is_valid:
        await websocket.close(code=1008, reason=error)
        return

    try:
        # Accept connection
        await ws_manager.connect(websocket, store_id)

        logger.info(f"WebSocket connected: store={store_id}")

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # For now, just log client messages
            # In production, could handle client commands here
            logger.debug(f"Received from {store_id}: {data}")

            # Echo back acknowledgment
            # await websocket.send_text(f"Received: {data}")

    except WebSocketDisconnect:
        # Clean disconnect from client
        ws_manager.disconnect(websocket, store_id)
        logger.info(f"WebSocket disconnected: store={store_id}")

    except Exception as e:
        # Unexpected error
        logger.error(f"WebSocket error for {store_id}: {e}")
        ws_manager.disconnect(websocket, store_id)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
