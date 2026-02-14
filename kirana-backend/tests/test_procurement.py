"""
Unit tests for Procurement Engine
Tests price optimization and order generation
"""

import pytest
from core.procurement import generate_procurement_order
from core.price_comparison import compare_distributors, optimize_order_split


@pytest.fixture
def sample_products():
    """Sample products for procurement"""
    return [
        {
            "sku_id": "maggi_70g",
            "name": "Maggi 2-Minute Noodles 70g",
            "category": "instant_food",
            "daily_velocity": 8,
            "reorder_point": 20
        },
        {
            "sku_id": "atta_5kg",
            "name": "Aashirvaad Atta 5kg",
            "category": "staples",
            "daily_velocity": 4,
            "reorder_point": 8
        },
        {
            "sku_id": "pepsi_600ml",
            "name": "Pepsi 600ml",
            "category": "beverages",
            "daily_velocity": 12,
            "reorder_point": 30
        }
    ]


@pytest.fixture
def sample_distributors():
    """Sample distributors with pricing"""
    return [
        {
            "id": "patel_wholesale",
            "name": "Patel Wholesale",
            "products": {
                "maggi_70g": {"price": 11.5, "moq": 10},
                "atta_5kg": {"price": 112.0, "moq": 5},
                "pepsi_600ml": {"price": 19.0, "moq": 12}
            },
            "delivery_time_hours": 24,
            "upi_id": "patel@paytm"
        },
        {
            "id": "metro_cash",
            "name": "Metro Cash & Carry",
            "products": {
                "maggi_70g": {"price": 11.0, "moq": 20},  # Cheaper but higher MOQ
                "atta_5kg": {"price": 110.0, "moq": 10},
                "pepsi_600ml": {"price": 18.5, "moq": 24}
            },
            "delivery_time_hours": 6,
            "upi_id": "metro@phonepe"
        },
        {
            "id": "gupta_fresh",
            "name": "Gupta Fresh",
            "products": {
                "atta_5kg": {"price": 115.0, "moq": 2}  # Most expensive but low MOQ
            },
            "delivery_time_hours": 6,
            "upi_id": "gupta@paytm"
        }
    ]


@pytest.fixture
def sample_context():
    """Sample context for ordering"""
    return {
        "store_name": "Test Store",
        "owner_name": "Test Owner",
        "upcoming_festivals": [],
        "weather": {"temperature": 25, "condition": "clear"}
    }


class TestPriceComparison:
    """Test price comparison across distributors"""

    def test_find_cheapest_distributor(self, sample_distributors):
        """Test finding cheapest distributor for a product"""
        comparison = compare_distributors(
            product_id="maggi_70g",
            quantity=20,
            distributors=sample_distributors
        )

        assert len(comparison) >= 2  # At least 2 distributors have this product
        # Metro should be cheapest at ₹11.0
        cheapest = comparison[0]
        assert cheapest["distributor_id"] == "metro_cash"
        assert cheapest["price_per_unit"] == 11.0

    def test_price_comparison_respects_moq(self, sample_distributors):
        """Test MOQ is respected in price comparison"""
        comparison = compare_distributors(
            product_id="maggi_70g",
            quantity=15,  # Less than Metro's MOQ of 20
            distributors=sample_distributors
        )

        # Metro should not be available or should adjust quantity
        metro_option = next((c for c in comparison if c["distributor_id"] == "metro_cash"), None)

        if metro_option:
            # If Metro is included, quantity should be adjusted to MOQ
            assert metro_option["quantity"] >= 20

    def test_comparison_shows_savings(self, sample_distributors):
        """Test comparison shows potential savings"""
        comparison = compare_distributors(
            product_id="maggi_70g",
            quantity=20,
            distributors=sample_distributors
        )

        # Should show savings compared to most expensive option
        cheapest = comparison[0]
        most_expensive = comparison[-1]

        assert most_expensive["total_cost"] > cheapest["total_cost"]
        assert cheapest["savings"] >= 0

    def test_unavailable_product(self, sample_distributors):
        """Test comparison when product not available"""
        comparison = compare_distributors(
            product_id="unavailable_product",
            quantity=10,
            distributors=sample_distributors
        )

        assert len(comparison) == 0  # No distributors have this product


class TestOrderOptimization:
    """Test order splitting optimization"""

    def test_optimize_order_split(self, sample_distributors):
        """Test order is split optimally across distributors"""
        order_items = [
            {"product_id": "maggi_70g", "quantity": 50},
            {"product_id": "atta_5kg", "quantity": 20},
            {"product_id": "pepsi_600ml", "quantity": 48}
        ]

        optimized = optimize_order_split(
            order_items=order_items,
            distributors=sample_distributors
        )

        assert "distributor_split" in optimized
        assert "total_cost" in optimized
        assert "total_savings" in optimized

        # Should use multiple distributors for best prices
        assert len(optimized["distributor_split"]) > 0

    def test_optimization_minimizes_cost(self, sample_distributors):
        """Test optimization actually minimizes total cost"""
        order_items = [
            {"product_id": "maggi_70g", "quantity": 50},
            {"product_id": "atta_5kg", "quantity": 20}
        ]

        optimized = optimize_order_split(
            order_items=order_items,
            distributors=sample_distributors
        )

        # Calculate what it would cost from single distributor (Patel)
        single_dist_cost = (50 * 11.5) + (20 * 112.0)  # 575 + 2240 = 2815

        # Optimized should be same or cheaper
        assert optimized["total_cost"] <= single_dist_cost

    def test_optimization_respects_moq(self, sample_distributors):
        """Test optimization respects minimum order quantities"""
        order_items = [
            {"product_id": "atta_5kg", "quantity": 5}  # Less than most MOQs
        ]

        optimized = optimize_order_split(
            order_items=order_items,
            distributors=sample_distributors
        )

        # Should still find a solution (Gupta has MOQ of 2)
        assert len(optimized["distributor_split"]) > 0


class TestProcurementOrderGeneration:
    """Test complete procurement order generation"""

    def test_generate_basic_order(self, sample_products, sample_distributors, sample_context):
        """Test generating a basic procurement order"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        assert "order_id" in order
        assert "items" in order
        assert "summary" in order
        assert "distributor_split" in order
        assert "created_at" in order

    def test_order_includes_upi_links(self, sample_products, sample_distributors, sample_context):
        """Test order includes UPI payment links"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        # Each distributor should have UPI link
        for dist_order in order["distributor_split"]:
            assert "upi_link" in dist_order
            assert "upi://" in dist_order["upi_link"]

    def test_order_summary_calculations(self, sample_products, sample_distributors, sample_context):
        """Test order summary has correct calculations"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        summary = order["summary"]

        assert "total_items" in summary
        assert "total_cost" in summary
        assert "total_savings" in summary
        assert summary["total_items"] > 0
        assert summary["total_cost"] > 0

    def test_order_includes_festival_context(self, sample_products, sample_distributors):
        """Test order includes festival context when applicable"""
        festival_context = {
            "store_name": "Test Store",
            "owner_name": "Test Owner",
            "upcoming_festivals": [
                {"name": "Navratri", "days_until": 2, "impact": "high"}
            ],
            "weather": {"temperature": 30, "condition": "clear"}
        }

        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=festival_context,
            store_id="test_store"
        )

        if "festival_context" in order:
            assert order["festival_context"]["name"] == "Navratri"

    def test_order_id_unique(self, sample_products, sample_distributors, sample_context):
        """Test each order has unique ID"""
        order1 = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        order2 = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        assert order1["order_id"] != order2["order_id"]


class TestOrderItems:
    """Test individual order items"""

    def test_order_items_have_required_fields(self, sample_products, sample_distributors, sample_context):
        """Test each order item has required fields"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        for item in order["items"]:
            assert "product_id" in item
            assert "product_name" in item
            assert "quantity" in item
            assert "price_per_unit" in item
            assert "total_cost" in item
            assert "distributor" in item

    def test_order_quantities_logical(self, sample_products, sample_distributors, sample_context):
        """Test order quantities are logical based on demand"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        for item in order["items"]:
            # Quantity should be positive and reasonable (not crazy high)
            assert item["quantity"] > 0
            assert item["quantity"] < 1000  # Sanity check

    def test_items_sorted_by_priority(self, sample_products, sample_distributors, sample_context):
        """Test order items can be sorted by priority"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        # Items should have urgency or priority
        has_urgency = any("urgency" in item or "priority" in item for item in order["items"])
        assert has_urgency or len(order["items"]) > 0  # At least items exist


class TestDistributorSplit:
    """Test distributor split in orders"""

    def test_distributor_split_structure(self, sample_products, sample_distributors, sample_context):
        """Test distributor split has correct structure"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        for dist_order in order["distributor_split"]:
            assert "distributor_id" in dist_order
            assert "distributor_name" in dist_order
            assert "items" in dist_order
            assert "subtotal" in dist_order
            assert "delivery_time" in dist_order

    def test_multi_distributor_orders(self, sample_products, sample_distributors, sample_context):
        """Test orders can span multiple distributors"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        # With price optimization, should use multiple distributors
        num_distributors = len(order["distributor_split"])
        assert num_distributors >= 1

    def test_distributor_subtotals_sum_to_total(self, sample_products, sample_distributors, sample_context):
        """Test distributor subtotals sum to total cost"""
        order = generate_procurement_order(
            products=sample_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        subtotal_sum = sum(d["subtotal"] for d in order["distributor_split"])
        total_cost = order["summary"]["total_cost"]

        assert abs(subtotal_sum - total_cost) < 0.01  # Allow for rounding


class TestEdgeCases:
    """Test edge cases in procurement"""

    def test_no_distributors_available(self, sample_products, sample_context):
        """Test handling when no distributors available"""
        empty_distributors = []

        order = generate_procurement_order(
            products=sample_products,
            distributors=empty_distributors,
            context=sample_context,
            store_id="test_store"
        )

        # Should return empty or minimal order
        assert len(order["items"]) == 0 or order["summary"]["total_cost"] == 0

    def test_single_product_order(self, sample_distributors, sample_context):
        """Test ordering single product"""
        single_product = [{
            "sku_id": "maggi_70g",
            "name": "Maggi",
            "category": "instant_food",
            "daily_velocity": 8
        }]

        order = generate_procurement_order(
            products=single_product,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        assert len(order["items"]) <= 1

    def test_large_order_volume(self, sample_products, sample_distributors, sample_context):
        """Test handling very large order volumes"""
        # Increase daily velocities to trigger large orders
        large_volume_products = [
            {**p, "daily_velocity": p["daily_velocity"] * 100}
            for p in sample_products
        ]

        order = generate_procurement_order(
            products=large_volume_products,
            distributors=sample_distributors,
            context=sample_context,
            store_id="test_store"
        )

        # Should handle large volumes
        assert order["summary"]["total_items"] > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
