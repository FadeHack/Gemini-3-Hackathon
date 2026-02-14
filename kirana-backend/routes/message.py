"""
Message API routes
Handles text, image, and voice message processing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from datetime import datetime
import uuid

from models.message import MessageInput, MessageResponse, ErrorResponse
from services.message_service import get_message_router
from services.gemini_service import get_gemini_service
from services.websocket_service import get_websocket_manager
from services.weather_service import get_weather_service
from core.inventory_engine import InventoryEngine
from core.demand_forecast import get_bulk_forecast
from core.procurement import generate_procurement_order
from core.festival_calendar import get_upcoming_festivals
from config.settings import settings
from utils.validators import validate_store_id
from utils.formatters import create_procurement_message
import json

router = APIRouter(prefix="/api", tags=["messages"])


async def process_message_background(
    message: MessageInput,
    message_id: str,
    store_id: str
):
    """
    Background task to process message and stream updates via WebSocket

    Args:
        message: Message input
        message_id: Unique message ID
        store_id: Store identifier
    """
    ws_manager = get_websocket_manager()
    gemini_service = get_gemini_service()
    weather_service = get_weather_service()

    try:
        # Load store data
        store_data_path = settings.get_store_path(store_id)
        with open(store_data_path, "r") as f:
            store_data = json.load(f)

        # Get weather context
        city = store_data.get("city", "Indore")
        weather = await weather_service.get_current_weather(city)

        # Get upcoming festivals
        festivals = get_upcoming_festivals(days_ahead=30)

        # Build context
        store_context = {
            "store_name": store_data.get("name", store_data.get("store_name", "")),
            "owner_name": store_data["owner_name"],
            "city": city,
            "language": message.language,
            "upcoming_festivals": festivals,
            "weather": weather
        }

        # Load product catalog
        with open(settings.PRODUCT_CATALOG_PATH, "r") as f:
            products_data = json.load(f)

        # Process based on message type
        if message.message_type == "text":
            # Send reasoning step
            await ws_manager.send_reasoning_step(
                store_id,
                "GENERAL_QUERY",
                "Processing your question...",
                {"query": message.content[:100]}
            )

            # Process with Gemini
            response = await gemini_service.process_text_query(
                message.content,
                store_context
            )

            # Send response
            await ws_manager.send_chat_message(
                store_id,
                response.message_to_owner,
                sender="assistant"
            )

        elif message.message_type == "image":
            # Detect if shelf photo or parchi (handwritten slip)
            # Check metadata hint or analyze image with Gemini
            is_parchi = False
            if hasattr(message, 'metadata') and message.metadata:
                is_parchi = message.metadata.get('image_type') == 'parchi'

            if is_parchi:
                # ====== PARCHI PROCESSING FLOW ======
                await ws_manager.send_reasoning_step(
                    store_id,
                    "PARCHI_READING",
                    "Reading handwritten parchi...",
                    icon="📝"
                )

                # Process with Gemini OCR
                response = await gemini_service.process_parchi_image(
                    message.content,
                    store_context,
                    products_data["products"]
                )

                # Extract transactions and update inventory
                if response.structured_data.get("transactions"):
                    inventory = store_data["current_inventory"]
                    engine = InventoryEngine(store_id, inventory)

                    transactions = response.structured_data["transactions"]
                    total_revenue = 0
                    total_items = 0

                    for txn in transactions:
                        # Apply each transaction to inventory
                        try:
                            result = engine.apply_transaction(
                                product_id=txn.get("product_id"),
                                quantity=-txn.get("quantity", 0),  # Negative for sales
                                transaction_type="sale",
                                price=txn.get("price"),
                                payment_type=txn.get("payment_type", "cash"),
                                customer_name=txn.get("customer_name")
                            )

                            # Send inventory update via WebSocket
                            await ws_manager.send_message(
                                store_id,
                                {
                                    "event_type": "inventory_update",
                                    "data": {
                                        "product_id": txn.get("product_id"),
                                        "product_name": txn.get("product_name"),
                                        "quantity_change": -txn.get("quantity", 0),
                                        "new_stock": result.get("new_stock", 0)
                                    }
                                }
                            )

                            total_revenue += txn.get("amount", 0)
                            total_items += txn.get("quantity", 0)

                        except Exception as e:
                            logger.warning(f"Failed to apply transaction: {e}")

                    # Send P&L update
                    await ws_manager.send_message(
                        store_id,
                        {
                            "event_type": "pnl_update",
                            "data": {
                                "revenue_change": total_revenue,
                                "items_sold": total_items
                            }
                        }
                    )

                    # Update udhaar if any credit sales
                    udhaar_total = sum(
                        txn.get("amount", 0)
                        for txn in transactions
                        if txn.get("payment_type") == "credit"
                    )
                    if udhaar_total > 0:
                        await ws_manager.send_message(
                            store_id,
                            {
                                "event_type": "udhaar_update",
                                "data": {"amount_change": udhaar_total}
                            }
                        )

                # Send response
                await ws_manager.send_chat_message(
                    store_id,
                    response.message_to_owner,
                    sender="assistant"
                )

            else:
                # ====== SHELF PHOTO PROCESSING FLOW ======
                await ws_manager.send_reasoning_step(
                    store_id,
                    "SHELF_ANALYSIS",
                    "Analyzing shelf photo...",
                    icon="🔍"
                )

                # Process with Gemini
                response = await gemini_service.process_shelf_photo(
                    message.content,
                    store_context,
                    products_data["products"]
                )

                # Extract detected products and update inventory
                if response.structured_data.get("products_detected"):
                    inventory = store_data["current_inventory"]
                    engine = InventoryEngine(store_id, inventory)

                    # Calibrate from detected products
                    detected = response.structured_data["products_detected"]
                    # (In production, would call engine.calibrate_from_shelf_photo)

                # Send response
                await ws_manager.send_chat_message(
                    store_id,
                    response.message_to_owner,
                    sender="assistant"
                )

                # Generate procurement if needed
                if response.structured_data.get("procurement_recommendations"):
                    await ws_manager.send_reasoning_step(
                        store_id,
                        "ORDER_GENERATION",
                        "Generating procurement order...",
                        icon="🛒"
                    )

                    # Load distributors
                    with open(settings.DISTRIBUTOR_PRICING_PATH, "r") as f:
                        distributors_data = json.load(f)

                    # Generate order
                    order = generate_procurement_order(
                        products=products_data["products"],
                        distributors=distributors_data["distributors"],
                        context=store_context,
                        store_id=store_id
                    )

                    if order.get("items"):
                        await ws_manager.send_procurement_order(store_id, order)

                        # Send formatted message
                        order_msg = create_procurement_message(
                            order_id=order["order_id"],
                            total_items=order["summary"]["total_items"],
                            total_cost=order["summary"]["total_cost"],
                            savings=order["summary"]["total_savings"],
                            distributor_count=len(order["distributor_split"]),
                            festival_name=order.get("festival_context", {}).get("name")
                        )
                        await ws_manager.send_chat_message(
                            store_id,
                            order_msg,
                            sender="assistant"
                        )

        elif message.message_type == "voice":
            await ws_manager.send_reasoning_step(
                store_id,
                "VOICE_PROCESSING",
                "Processing voice message...",
                icon="🎤"
            )

            # Process with Gemini
            response = await gemini_service.process_voice_message(
                message.content,
                store_context
            )

            # Send response
            await ws_manager.send_chat_message(
                store_id,
                response.message_to_owner,
                sender="assistant"
            )

    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}")
        await ws_manager.send_error(
            store_id,
            f"Error processing message: {str(e)}"
        )


@router.post(
    "/message",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_message(
    message: MessageInput,
    background_tasks: BackgroundTasks
):
    """
    Process incoming message (text, image, or voice)

    This endpoint accepts a message and immediately returns a response with
    a WebSocket URL for real-time updates. The actual processing happens
    in the background and streams results via WebSocket.

    **Request Body:**
    - `store_id`: Store identifier
    - `message_type`: Type of message (text, image, voice)
    - `content`: Message content (text or base64 encoded media)
    - `language`: Language preference (default: hinglish)

    **Response:**
    - `message_id`: Unique identifier for tracking
    - `status`: Processing status (processing)
    - `websocket_channel`: WebSocket URL for real-time updates
    - `timestamp`: Message receipt timestamp

    **Example:**
    ```json
    {
      "store_id": "sharma_general_store",
      "message_type": "text",
      "content": "Maggi ka stock kitna hai?"
    }
    ```
    """
    router = get_message_router()

    try:
        # Validate message
        is_valid, error = router.validate_message(message)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error
            )

        # Validate store_id
        is_valid, error = validate_store_id(message.store_id)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error
            )

        # Generate message ID
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Get WebSocket channel URL
        websocket_url = f"ws://localhost:{settings.PORT}/ws/{message.store_id}"

        # Create response
        response = MessageResponse(
            message_id=message_id,
            status="processing",
            websocket_channel=websocket_url,
            timestamp=datetime.now().isoformat()
        )

        # Process message in background
        background_tasks.add_task(
            process_message_background,
            message,
            message_id,
            message.store_id
        )

        logger.info(
            f"Message queued: {message_id}, type={message.message_type}, "
            f"store={message.store_id}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
