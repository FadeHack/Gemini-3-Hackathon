"""
Test script to validate all Pydantic models
"""

import json
from pathlib import Path
from datetime import datetime

# Import all models
from models.store import (
    Product, StoreProfile, Distributor, InventoryItem,
    UdhaarCustomer, DailySummary, StorePreferences, StoreMetadata
)
from models.message import MessageInput, MessageResponse, ErrorResponse
from models.inventory import Transaction, InventoryAlert, InventoryUpdate
from models.procurement import (
    ProcurementItem, ProcurementOrder, DistributorSplit,
    UPIDeeplink, OrderSummary, PriceComparison
)
from models.websocket import (
    WebSocketEvent, ReasoningStepEvent, ChatMessageEvent,
    InventoryUpdateEvent, ErrorEvent
)
from models.gemini import ReasoningStep, GeminiResponse, UncertainItem


def test_message_models():
    """Test message input/output models"""
    print("Testing Message Models...")

    # Test MessageInput
    msg_input = MessageInput(
        store_id="sharma_general_store",
        message_type="text",
        content="Maggi ka stock kitna hai?",
        language="hinglish"
    )
    assert msg_input.store_id == "sharma_general_store"
    print("  ✅ MessageInput")

    # Test MessageResponse
    msg_response = MessageResponse(
        message_id="msg_123",
        status="processing",
        websocket_channel="ws://localhost:8000/ws/sharma_general_store",
        timestamp=datetime.now().isoformat()
    )
    assert msg_response.status == "processing"
    print("  ✅ MessageResponse")

    # Test ErrorResponse
    error = ErrorResponse(
        error="invalid_store",
        message="Store not found",
        timestamp=datetime.now().isoformat()
    )
    assert error.error == "invalid_store"
    print("  ✅ ErrorResponse")


def test_inventory_models():
    """Test inventory-related models"""
    print("\nTesting Inventory Models...")

    # Test Transaction
    txn = Transaction(
        transaction_id="txn_001",
        product_id="maggi_70g",
        product_name="Maggi 70g",
        quantity_change=-5,
        transaction_type="cash",
        price=70.0,
        timestamp=datetime.now().isoformat(),
        source="kacchi_parchi"
    )
    assert txn.quantity_change == -5
    print("  ✅ Transaction")

    # Test InventoryAlert
    alert = InventoryAlert(
        product_id="maggi_70g",
        product_name="Maggi 2-Minute Noodles 70g",
        product_name_local="मैगी नूडल्स",
        current_stock=3,
        days_remaining=0.375,
        status="critical",
        message="Stock critically low",
        urgency="critical",
        action_required=True,
        recommended_order_qty=25
    )
    assert alert.status == "critical"
    print("  ✅ InventoryAlert")


def test_procurement_models():
    """Test procurement models"""
    print("\nTesting Procurement Models...")

    # Test ProcurementItem
    item = ProcurementItem(
        product_id="maggi_70g",
        name="Maggi 70g",
        name_local="मैगी",
        quantity=25,
        unit="packets",
        best_distributor="Patel Wholesale",
        distributor_id="patel_wholesale",
        unit_price=11.5,
        total_price=287.5,
        mrp=14.0,
        savings_per_unit=2.5,
        urgency="critical",
        reason="Only 3 packets left",
        days_of_stock=0.375,
        recommended_by="inventory_alert"
    )
    assert item.quantity == 25
    print("  ✅ ProcurementItem")

    # Test OrderSummary
    summary = OrderSummary(
        total_items=12,
        total_quantity=125,
        total_cost=3847.50,
        total_mrp_value=4850.00,
        total_savings=1002.50,
        savings_percentage=20.7
    )
    assert summary.total_items == 12
    print("  ✅ OrderSummary")


def test_websocket_models():
    """Test WebSocket event models"""
    print("\nTesting WebSocket Models...")

    # Test WebSocketEvent
    event = WebSocketEvent(
        event="chat_message",
        data={"message": "Hello"},
        timestamp=datetime.now().isoformat()
    )
    assert event.event == "chat_message"
    print("  ✅ WebSocketEvent")

    # Test ReasoningStepEvent
    reasoning = ReasoningStepEvent(
        data={
            "step_number": 1,
            "step_type": "SHELF_ANALYSIS",
            "icon": "🔍",
            "title": "Analyzing shelf",
            "description": "Processing image...",
            "details": {}
        },
        timestamp=datetime.now().isoformat()
    )
    assert reasoning.event == "reasoning_step"
    print("  ✅ ReasoningStepEvent")


def test_gemini_models():
    """Test Gemini response models"""
    print("\nTesting Gemini Models...")

    # Test ReasoningStep
    step = ReasoningStep(
        step_number=1,
        step_type="SHELF_ANALYSIS",
        icon="🔍",
        title="Shelf Analysis",
        description="Analyzing shelf photo",
        details={"products_detected": 15},
        status="completed",
        timestamp=datetime.now().isoformat()
    )
    assert step.step_number == 1
    print("  ✅ ReasoningStep")

    # Test GeminiResponse
    response = GeminiResponse(
        response_type="shelf_analysis",
        reasoning_steps=[step],
        message_to_owner="Rajesh bhai, aapki shelf dekhi...",
    )
    assert response.response_type == "shelf_analysis"
    assert len(response.reasoning_steps) == 1
    print("  ✅ GeminiResponse")


def test_store_models_with_real_data():
    """Test store models with actual JSON data"""
    print("\nTesting Store Models with Real Data...")

    # Load real product data
    with open("data/products.json", "r", encoding="utf-8") as f:
        products_data = json.load(f)

    # Validate each product
    for product_data in products_data["products"]:
        product = Product(**product_data)
        assert product.sku_id
        assert product.mrp > 0

    print(f"  ✅ Validated {len(products_data['products'])} products")

    # Load distributor data
    with open("data/distributors.json", "r", encoding="utf-8") as f:
        dist_data = json.load(f)

    # Validate each distributor
    for dist in dist_data["distributors"]:
        distributor = Distributor(**dist)
        assert distributor.id
        assert len(distributor.products) > 0

    print(f"  ✅ Validated {len(dist_data['distributors'])} distributors")

    # Load store profile
    with open("data/stores/sharma_general_store.json", "r", encoding="utf-8") as f:
        store_data = json.load(f)

    # Create StoreProfile (this will validate all nested models)
    store = StoreProfile(**store_data)
    assert store.store_id == "sharma_general_store"
    assert store.owner_name == "Rajesh Sharma"
    assert len(store.current_inventory) == 20

    print(f"  ✅ Validated StoreProfile with {len(store.current_inventory)} inventory items")


def main():
    print("=" * 60)
    print("KiranaGPT Backend - Pydantic Models Validation")
    print("=" * 60)
    print()

    try:
        test_message_models()
        test_inventory_models()
        test_procurement_models()
        test_websocket_models()
        test_gemini_models()
        test_store_models_with_real_data()

        print()
        print("=" * 60)
        print("✅ All model tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
