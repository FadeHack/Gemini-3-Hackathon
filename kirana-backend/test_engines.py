"""
Test script for core engines
"""

import json
from datetime import datetime, timedelta
from core.inventory_engine import InventoryEngine
from core.demand_forecast import get_demand_forecast, get_bulk_forecast
from core.price_comparison import compare_distributors, optimize_order_split
from core.procurement import generate_procurement_order
from core.festival_calendar import get_upcoming_festivals, get_festival_multiplier


def load_test_data():
    """Load test data from JSON files"""
    with open("data/products.json", "r") as f:
        products_data = json.load(f)
    with open("data/distributors.json", "r") as f:
        distributors_data = json.load(f)
    with open("data/stores/sharma_general_store.json", "r") as f:
        store_data = json.load(f)

    return products_data, distributors_data, store_data


def test_inventory_engine():
    """Test InventoryEngine"""
    print("Testing InventoryEngine...")

    # Load store data
    _, _, store_data = load_test_data()
    inventory = store_data["current_inventory"]

    # Initialize engine
    engine = InventoryEngine("sharma_general_store", inventory)
    assert len(engine.inventory) == 20
    print(f"  ✅ Initialized with {len(engine.inventory)} products")

    # Test sale transaction (sell 2, we only have 3 in stock)
    result = engine.apply_transaction(
        product_id="maggi_70g",
        quantity_change=-2,
        transaction_type="cash",
        price=28.0,
        source="test"
    )
    assert result["status"] == "ok"
    assert result["change"] == -2
    assert len(result["alerts"]) > 0  # Should have critical stock alert
    print(f"  ✅ Sale transaction: {result['old_stock']} → {result['new_stock']}")

    # Test delivery transaction
    result = engine.apply_transaction(
        product_id="maggi_70g",
        quantity_change=48,
        transaction_type="supplier_delivery",
        source="test"
    )
    assert result["status"] == "ok"
    assert result["change"] == 48
    print(f"  ✅ Delivery transaction applied")

    # Test daily summary
    summary = engine.get_daily_summary()
    assert summary["total_revenue"] > 0
    assert summary["items_sold"] > 0
    print(f"  ✅ Daily summary: ₹{summary['total_revenue']:.2f} revenue, {summary['items_sold']} items sold")

    # Test low stock detection
    low_stock = engine.get_low_stock_items(threshold_days=5.0)
    assert len(low_stock) > 0
    print(f"  ✅ Low stock detection: {len(low_stock)} items need attention")


def test_demand_forecast():
    """Test demand forecasting"""
    print("\nTesting Demand Forecast...")

    products_data, _, store_data = load_test_data()

    # Get a product with festival boost (sabudana)
    product = next(p for p in products_data["products"] if p["sku_id"] == "sabudana_500g")

    # Add inventory state
    product["current_stock"] = store_data["current_inventory"]["sabudana_500g"]["current_stock"]

    # Create context with upcoming Navratri
    context = {
        "upcoming_festivals": [{
            "id": "navratri",
            "name": "Navratri",
            "starts": (datetime.now() + timedelta(days=2)).isoformat(),
            "start_date": (datetime.now() + timedelta(days=2)).date().isoformat(),
            "duration_days": 9
        }],
        "weather": {"temp_c": 28, "condition": "clear"},
        "current_date": datetime.now()
    }

    forecast = get_demand_forecast(product, days=7, context=context)

    assert forecast["product_id"] == "sabudana_500g"
    assert forecast["has_festival_impact"] == True  # Should be affected by Navratri
    assert len(forecast["daily_forecasts"]) == 7
    print(f"  ✅ Forecast for {forecast['product_name']}")
    print(f"     Days of stock: {forecast['days_of_stock_forecast']:.1f}")
    print(f"     Recommended order: {forecast['recommended_order_qty']}")
    print(f"     Festival impact: {forecast['has_festival_impact']}")


def test_price_comparison():
    """Test price comparison"""
    print("\nTesting Price Comparison...")

    _, distributors_data, _ = load_test_data()
    distributors = distributors_data["distributors"]

    # Compare prices for Maggi
    comparison = compare_distributors("maggi_70g", distributors)

    assert comparison is not None
    assert comparison["product_id"] == "maggi_70g"
    assert comparison["cheapest"]["price"] <= comparison["most_expensive"]["price"]
    print(f"  ✅ Maggi price comparison:")
    print(f"     Cheapest: ₹{comparison['cheapest']['price']} from {comparison['cheapest']['distributor_name']}")
    print(f"     Savings: ₹{comparison['savings']:.2f} ({comparison['savings_pct']:.1f}%)")

    # Test order optimization
    items = [
        {"product_id": "maggi_70g", "quantity": 25},
        {"product_id": "sabudana_500g", "quantity": 18},
        {"product_id": "surf_excel_1kg", "quantity": 10}
    ]

    optimization = optimize_order_split(items, distributors)

    assert len(optimization["optimized_items"]) == 3
    assert optimization["distributors_used"] >= 1
    print(f"  ✅ Order optimization:")
    print(f"     Total cost: ₹{optimization['total_cost']:.2f}")
    print(f"     Distributors used: {optimization['distributors_used']}")
    print(f"     Savings vs single: ₹{optimization['savings_vs_single']:.2f}")


def test_festival_calendar():
    """Test festival calendar utilities"""
    print("\nTesting Festival Calendar...")

    # Get upcoming festivals
    upcoming = get_upcoming_festivals(days_ahead=60)

    assert len(upcoming) > 0
    print(f"  ✅ Found {len(upcoming)} upcoming festivals")
    if upcoming:
        print(f"     Next: {upcoming[0]['name']} in {upcoming[0]['days_until']} days")

    # Test multiplier lookup
    navratri_mult = get_festival_multiplier("navratri", "fasting_food")
    assert navratri_mult == 3.5
    print(f"  ✅ Navratri fasting_food multiplier: {navratri_mult}x")


def test_procurement_engine():
    """Test full procurement order generation"""
    print("\nTesting Procurement Engine...")

    products_data, distributors_data, store_data = load_test_data()

    # Build products with current inventory
    products = []
    for product in products_data["products"][:10]:  # Use first 10 for speed
        inv_data = store_data["current_inventory"].get(product["sku_id"], {})
        product_copy = {**product}
        product_copy["current_stock"] = inv_data.get("current_stock", 0)
        products.append(product_copy)

    distributors = distributors_data["distributors"]

    # Create context with upcoming festival
    context = {
        "upcoming_festivals": [{
            "id": "navratri",
            "name": "Navratri",
            "starts": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_days": 9,
            "impact_level": "high"
        }],
        "weather": {"temp_c": 32, "condition": "clear"},
        "current_date": datetime.now()
    }

    order = generate_procurement_order(
        products=products,
        distributors=distributors,
        context=context,
        store_id="sharma_general_store",
        forecast_days=7
    )

    if order.get("items"):
        assert order["order_id"] is not None
        assert len(order["items"]) > 0
        assert order["summary"]["total_cost"] > 0
        print(f"  ✅ Procurement order generated:")
        print(f"     Order ID: {order['order_id']}")
        print(f"     Items: {order['summary']['total_items']}")
        print(f"     Total cost: ₹{order['summary']['total_cost']:.2f}")
        print(f"     Savings: ₹{order['summary']['total_savings']:.2f} ({order['summary']['savings_percentage']:.1f}%)")
        print(f"     Distributors: {len(order['distributor_split'])}")
        if order.get("festival_context"):
            print(f"     Festival: {order['festival_context']['name']}")
    else:
        print(f"  ✅ No items need ordering (all stock sufficient)")


def main():
    print("=" * 60)
    print("KiranaGPT Backend - Core Engines Testing")
    print("=" * 60)
    print()

    try:
        test_inventory_engine()
        test_demand_forecast()
        test_price_comparison()
        test_festival_calendar()
        test_procurement_engine()

        print()
        print("=" * 60)
        print("✅ All engine tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Engine test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
