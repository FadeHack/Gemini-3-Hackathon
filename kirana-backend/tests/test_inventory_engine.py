"""
Unit tests for InventoryEngine
Tests transaction processing, stock alerts, and daily summaries
"""

import pytest
from datetime import datetime, date
from core.inventory_engine import InventoryEngine


@pytest.fixture
def sample_inventory():
    """Sample inventory data for testing"""
    return [
        {
            "product_id": "maggi_70g",
            "current_stock": 10,
            "reorder_point": 5,
            "price": 12.0
        },
        {
            "product_id": "atta_5kg",
            "current_stock": 20,
            "reorder_point": 8,
            "price": 115.0
        },
        {
            "product_id": "parle_g",
            "current_stock": 2,  # Already low stock
            "reorder_point": 5,
            "price": 5.0
        }
    ]


@pytest.fixture
def engine(sample_inventory):
    """Create InventoryEngine instance with sample data"""
    return InventoryEngine("test_store", sample_inventory)


class TestInventoryEngineInitialization:
    """Test InventoryEngine initialization"""

    def test_initialization_with_valid_data(self, engine):
        """Test engine initializes correctly with valid data"""
        assert engine.store_id == "test_store"
        assert len(engine.inventory) == 3
        assert engine.inventory["maggi_70g"]["current_stock"] == 10

    def test_initialization_creates_transaction_log(self, engine):
        """Test transaction log is initialized"""
        assert hasattr(engine, 'transaction_log')
        assert isinstance(engine.transaction_log, list)


class TestTransactionProcessing:
    """Test transaction processing"""

    def test_sale_transaction_reduces_stock(self, engine):
        """Test sale transaction reduces stock correctly"""
        result = engine.apply_transaction(
            product_id="maggi_70g",
            quantity=-5,  # Negative for sales
            transaction_type="sale",
            price=12.0,
            payment_type="cash"
        )

        assert result["success"] is True
        assert result["new_stock"] == 5
        assert engine.inventory["maggi_70g"]["current_stock"] == 5

    def test_delivery_transaction_increases_stock(self, engine):
        """Test delivery transaction increases stock correctly"""
        result = engine.apply_transaction(
            product_id="maggi_70g",
            quantity=50,  # Positive for deliveries
            transaction_type="supplier_delivery",
            price=11.0
        )

        assert result["success"] is True
        assert result["new_stock"] == 60
        assert engine.inventory["maggi_70g"]["current_stock"] == 60

    def test_insufficient_stock_prevents_sale(self, engine):
        """Test cannot sell more than available stock"""
        with pytest.raises(ValueError, match="Insufficient stock"):
            engine.apply_transaction(
                product_id="maggi_70g",
                quantity=-15,  # More than available
                transaction_type="sale",
                price=12.0
            )

    def test_invalid_product_raises_error(self, engine):
        """Test transaction with invalid product raises error"""
        with pytest.raises(ValueError, match="not found"):
            engine.apply_transaction(
                product_id="invalid_product",
                quantity=-5,
                transaction_type="sale",
                price=10.0
            )

    def test_transaction_logged(self, engine):
        """Test transactions are logged"""
        initial_log_count = len(engine.transaction_log)

        engine.apply_transaction(
            product_id="maggi_70g",
            quantity=-3,
            transaction_type="sale",
            price=12.0,
            payment_type="upi"
        )

        assert len(engine.transaction_log) == initial_log_count + 1
        last_transaction = engine.transaction_log[-1]
        assert last_transaction["product_id"] == "maggi_70g"
        assert last_transaction["quantity"] == -3
        assert last_transaction["payment_type"] == "upi"

    def test_udhaar_transaction(self, engine):
        """Test credit (udhaar) transaction"""
        result = engine.apply_transaction(
            product_id="atta_5kg",
            quantity=-2,
            transaction_type="sale",
            price=115.0,
            payment_type="credit",
            customer_name="Ramesh"
        )

        assert result["success"] is True
        last_transaction = engine.transaction_log[-1]
        assert last_transaction["payment_type"] == "credit"
        assert last_transaction["customer_name"] == "Ramesh"


class TestStockAlerts:
    """Test stock alert generation"""

    def test_critical_stock_alert(self, engine):
        """Test critical stock alert when below reorder point"""
        # Reduce Maggi to 3 (below reorder_point of 5)
        engine.apply_transaction(
            product_id="maggi_70g",
            quantity=-7,
            transaction_type="sale",
            price=12.0
        )

        alerts = engine.get_low_stock_alerts()

        assert len(alerts) >= 2  # Maggi + Parle-G (already low)
        maggi_alert = next(a for a in alerts if a["product_id"] == "maggi_70g")
        assert maggi_alert["urgency"] in ["critical", "warning"]
        assert maggi_alert["current_stock"] == 3

    def test_no_alerts_when_stock_healthy(self, engine):
        """Test no alerts when all stock is healthy"""
        # Add stock to parle_g to make it healthy
        engine.apply_transaction(
            product_id="parle_g",
            quantity=20,
            transaction_type="supplier_delivery",
            price=4.5
        )

        alerts = engine.get_low_stock_alerts()

        # Should have no critical alerts
        assert len(alerts) == 0 or all(a["urgency"] != "critical" for a in alerts)

    def test_alert_urgency_levels(self, engine):
        """Test different urgency levels based on stock"""
        # Create critical stock (< 1 day)
        engine.inventory["maggi_70g"]["current_stock"] = 1
        engine.inventory["maggi_70g"]["daily_velocity"] = 5

        # Create warning stock (1-3 days)
        engine.inventory["atta_5kg"]["current_stock"] = 10
        engine.inventory["atta_5kg"]["daily_velocity"] = 4

        alerts = engine.get_low_stock_alerts()

        maggi_alert = next((a for a in alerts if a["product_id"] == "maggi_70g"), None)
        atta_alert = next((a for a in alerts if a["product_id"] == "atta_5kg"), None)

        if maggi_alert:
            assert maggi_alert["urgency"] == "critical"
        if atta_alert:
            assert atta_alert["urgency"] in ["warning", "medium"]


class TestDailySummary:
    """Test daily summary generation"""

    def test_daily_summary_structure(self, engine):
        """Test daily summary has correct structure"""
        # Make some transactions
        engine.apply_transaction("maggi_70g", -3, "sale", 12.0, "cash")
        engine.apply_transaction("atta_5kg", -1, "sale", 115.0, "upi")
        engine.apply_transaction("parle_g", 20, "supplier_delivery", 4.5)

        summary = engine.get_daily_summary()

        assert "date" in summary
        assert "total_revenue" in summary
        assert "items_sold" in summary
        assert "items_received" in summary
        assert "cash_collected" in summary
        assert "upi_collected" in summary
        assert "credit_given" in summary

    def test_daily_summary_calculations(self, engine):
        """Test daily summary calculates correctly"""
        # Cash sale: 3 × ₹12 = ₹36
        engine.apply_transaction("maggi_70g", -3, "sale", 12.0, "cash")

        # UPI sale: 1 × ₹115 = ₹115
        engine.apply_transaction("atta_5kg", -1, "sale", 115.0, "upi")

        # Credit sale: 2 × ₹5 = ₹10
        engine.apply_transaction("parle_g", -2, "sale", 5.0, "credit", "Ramesh")

        summary = engine.get_daily_summary()

        assert summary["total_revenue"] == 36 + 115 + 10  # 161
        assert summary["cash_collected"] == 36
        assert summary["upi_collected"] == 115
        assert summary["credit_given"] == 10
        assert summary["items_sold"] == 6  # 3 + 1 + 2

    def test_daily_summary_filters_by_date(self, engine):
        """Test daily summary only includes today's transactions"""
        today = date.today()

        # Make a transaction
        engine.apply_transaction("maggi_70g", -5, "sale", 12.0, "cash")

        summary = engine.get_daily_summary(date=today)

        assert summary["items_sold"] == 5
        assert summary["total_revenue"] == 60


class TestInventoryState:
    """Test inventory state management"""

    def test_get_current_stock(self, engine):
        """Test retrieving current stock for a product"""
        stock = engine.get_current_stock("maggi_70g")
        assert stock == 10

    def test_get_inventory_value(self, engine):
        """Test calculating total inventory value"""
        # Maggi: 10 × 12 = 120
        # Atta: 20 × 115 = 2300
        # Parle-G: 2 × 5 = 10
        # Total = 2430

        total_value = engine.get_inventory_value()
        assert total_value == 2430.0

    def test_days_of_stock_calculation(self, engine):
        """Test days of stock calculation"""
        engine.inventory["maggi_70g"]["daily_velocity"] = 5
        engine.inventory["maggi_70g"]["current_stock"] = 10

        days = engine.calculate_days_of_stock("maggi_70g")
        assert days == 2.0  # 10 / 5 = 2 days


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_quantity_transaction(self, engine):
        """Test transaction with zero quantity"""
        with pytest.raises(ValueError):
            engine.apply_transaction("maggi_70g", 0, "sale", 12.0)

    def test_negative_price(self, engine):
        """Test transaction with negative price"""
        # Should still work (could be return/refund scenario)
        result = engine.apply_transaction("maggi_70g", 5, "return", -12.0)
        assert result["success"] is True

    def test_very_large_delivery(self, engine):
        """Test delivery with very large quantity"""
        result = engine.apply_transaction(
            "maggi_70g",
            quantity=10000,
            transaction_type="supplier_delivery",
            price=11.0
        )

        assert result["success"] is True
        assert engine.inventory["maggi_70g"]["current_stock"] == 10010

    def test_empty_customer_name_for_credit(self, engine):
        """Test credit sale without customer name"""
        # Should work but log warning
        result = engine.apply_transaction(
            "maggi_70g",
            quantity=-2,
            transaction_type="sale",
            price=12.0,
            payment_type="credit",
            customer_name=None
        )

        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
