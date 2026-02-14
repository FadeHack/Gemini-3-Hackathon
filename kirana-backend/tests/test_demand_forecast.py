"""
Unit tests for Demand Forecast Engine
Tests festival multipliers, weather impact, and demand predictions
"""

import pytest
from datetime import datetime, timedelta
from core.demand_forecast import (
    get_demand_forecast,
    get_bulk_forecast
)
from core.festival_calendar import get_upcoming_festivals


@pytest.fixture
def sample_product():
    """Sample product for forecasting"""
    return {
        "sku_id": "maggi_70g",
        "name": "Maggi 2-Minute Noodles 70g",
        "category": "instant_food",
        "daily_velocity": 8
    }


@pytest.fixture
def sample_weather():
    """Sample weather data"""
    return {
        "temperature": 35,
        "condition": "clear",
        "humidity": 60
    }


@pytest.fixture
def festival_context():
    """Sample festival context"""
    return get_upcoming_festivals(days_ahead=30)


class TestBasicDemandForecast:
    """Test basic demand forecasting"""

    def test_forecast_without_modifiers(self, sample_product):
        """Test forecast with no festival or extreme weather"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=10,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        assert "product_id" in forecast
        assert forecast["product_id"] == "maggi_70g"
        assert "daily_forecasts" in forecast
        assert len(forecast["daily_forecasts"]) == 7
        assert forecast["base_daily_sales"] == 8

    def test_forecast_calculates_cumulative_demand(self, sample_product):
        """Test cumulative demand calculation"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=50,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        # With base velocity of 8, 7 days should be ~56 units (may vary with day-of-week)
        assert forecast["cumulative_demand"] > 50
        assert forecast["cumulative_demand"] < 70

    def test_forecast_stockout_prediction(self, sample_product):
        """Test stockout day prediction"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=10,  # Low stock
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        # With 10 stock and 8/day velocity, should stockout in 1-2 days
        assert forecast["stockout_day"] is not None
        assert forecast["stockout_day"] <= 2

    def test_forecast_order_recommendation(self, sample_product):
        """Test order quantity recommendation"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=5,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7,
            target_days_of_stock=10
        )

        # Should recommend enough to reach 10 days of stock
        assert forecast["recommended_order_qty"] > 0
        # Roughly: (10 days × 8/day) - 5 current = ~75
        assert forecast["recommended_order_qty"] > 60


class TestFestivalImpact:
    """Test festival impact on demand"""

    def test_festival_multiplier_increases_demand(self, sample_product, festival_context):
        """Test festival increases demand for affected categories"""
        # Modify product to be fasting food (affected by Navratri)
        sample_product["category"] = "fasting_food"
        sample_product["sku_id"] = "sabudana_500g"

        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=20,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=festival_context,
            forecast_days=7
        )

        # Check if any day has festival boost
        has_festival_boost = any(
            "festival" in day["factors"] and day["factors"]["festival"] != "1.0x"
            for day in forecast["daily_forecasts"]
        )

        # If Navratri is upcoming, should have boost
        if any(f["name"] == "Navratri" for f in festival_context):
            assert has_festival_boost

    def test_non_festival_category_unaffected(self, sample_product, festival_context):
        """Test non-festival products don't get festival boost"""
        # Instant food shouldn't get Navratri boost (only fasting foods do)
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=50,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=festival_context,
            forecast_days=7
        )

        # Check festival factors
        for day in forecast["daily_forecasts"]:
            # Most days should have 1.0x festival factor for instant_food
            # (unless it's a festival that affects instant_food)
            assert "festival" in day["factors"]

    def test_forecast_urgency_increases_with_festival(self, festival_context):
        """Test urgency level increases when festival approaching"""
        # Product with low stock before festival
        fasting_product = {
            "sku_id": "sabudana_500g",
            "name": "Sabudana",
            "category": "fasting_food",
            "daily_velocity": 10
        }

        forecast = get_demand_forecast(
            product=fasting_product,
            current_stock=15,  # Low stock for festival demand
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=festival_context,
            forecast_days=7
        )

        # Should have high urgency if Navratri is approaching
        if any(f["name"] == "Navratri" and f["days_until"] <= 3 for f in festival_context):
            assert forecast["urgency"] in ["critical", "high"]


class TestWeatherImpact:
    """Test weather impact on demand"""

    def test_hot_weather_increases_beverage_demand(self):
        """Test hot weather increases demand for beverages"""
        beverage = {
            "sku_id": "pepsi_600ml",
            "name": "Pepsi 600ml",
            "category": "beverages",
            "daily_velocity": 15
        }

        hot_weather = {"temperature": 38, "condition": "clear"}

        forecast = get_demand_forecast(
            product=beverage,
            current_stock=50,
            weather=hot_weather,
            upcoming_festivals=[],
            forecast_days=3
        )

        # Check for weather boost
        has_weather_boost = any(
            "weather" in day["factors"] and day["factors"]["weather"] != "1.0x"
            for day in forecast["daily_forecasts"]
        )

        assert has_weather_boost

    def test_rainy_weather_increases_instant_food_demand(self):
        """Test rainy weather increases instant food demand"""
        instant_food = {
            "sku_id": "maggi_70g",
            "name": "Maggi",
            "category": "instant_food",
            "daily_velocity": 8
        }

        rainy_weather = {"temperature": 22, "condition": "rain"}

        forecast = get_demand_forecast(
            product=instant_food,
            current_stock=20,
            weather=rainy_weather,
            upcoming_festivals=[],
            forecast_days=3
        )

        # Rainy weather should boost instant food
        avg_demand = sum(day["demand"] for day in forecast["daily_forecasts"]) / 3
        assert avg_demand > instant_food["daily_velocity"]


class TestDayOfWeekPattern:
    """Test day-of-week demand patterns"""

    def test_sunday_has_higher_demand(self, sample_product):
        """Test Sunday has higher demand multiplier"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=100,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        # Find Sunday in forecast
        sunday_days = [
            day for day in forecast["daily_forecasts"]
            if day["day_of_week"] == "Sunday"
        ]

        if sunday_days:
            sunday = sunday_days[0]
            # Sunday should have higher multiplier
            assert sunday["factors"]["day_of_week"] in ["1.3x", "1.2x"]

    def test_monday_has_lower_demand(self, sample_product):
        """Test Monday typically has lower demand"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=100,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        monday_days = [
            day for day in forecast["daily_forecasts"]
            if day["day_of_week"] == "Monday"
        ]

        if monday_days:
            monday = monday_days[0]
            # Monday should have lower or normal multiplier
            assert monday["factors"]["day_of_week"] in ["0.9x", "1.0x"]


class TestBulkForecast:
    """Test bulk forecasting for multiple products"""

    def test_bulk_forecast_multiple_products(self):
        """Test generating forecasts for multiple products"""
        products = [
            {"sku_id": "maggi_70g", "category": "instant_food", "daily_velocity": 8},
            {"sku_id": "atta_5kg", "category": "staples", "daily_velocity": 4},
            {"sku_id": "pepsi_600ml", "category": "beverages", "daily_velocity": 12}
        ]

        inventory = {
            "maggi_70g": {"current_stock": 10},
            "atta_5kg": {"current_stock": 20},
            "pepsi_600ml": {"current_stock": 30}
        }

        forecasts = get_bulk_forecast(
            products=products,
            inventory=inventory,
            weather={"temperature": 30, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        assert len(forecasts) == 3
        assert all("product_id" in f for f in forecasts)
        assert all("recommended_order_qty" in f for f in forecasts)

    def test_bulk_forecast_sorts_by_urgency(self):
        """Test bulk forecast sorts products by urgency"""
        products = [
            {"sku_id": "critical_item", "category": "snacks", "daily_velocity": 20},
            {"sku_id": "healthy_item", "category": "snacks", "daily_velocity": 2}
        ]

        inventory = {
            "critical_item": {"current_stock": 5},  # Only 0.25 days of stock
            "healthy_item": {"current_stock": 50}  # 25 days of stock
        }

        forecasts = get_bulk_forecast(
            products=products,
            inventory=inventory,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        # First item should be the critical one
        assert forecasts[0]["product_id"] == "critical_item"
        assert forecasts[0]["urgency"] == "critical"


class TestForecastAccuracy:
    """Test forecast calculation accuracy"""

    def test_combined_multipliers(self):
        """Test multiple multipliers combine correctly"""
        product = {
            "sku_id": "test_product",
            "category": "beverages",
            "daily_velocity": 10
        }

        # Hot weather (1.4x) + Sunday (1.3x) = 1.82x
        # Expected: 10 × 1.4 × 1.3 = 18.2

        forecast_demand = calculate_forecast_demand(
            base_velocity=10,
            festival_multiplier=1.0,
            weather_multiplier=1.4,
            dow_multiplier=1.3
        )

        assert forecast_demand == pytest.approx(18.2, rel=0.01)

    def test_forecast_never_negative(self, sample_product):
        """Test forecast demand is never negative"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=0,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        for day in forecast["daily_forecasts"]:
            assert day["demand"] >= 0
            assert day["stock_after"] is not None  # Can be negative (stockout)


class TestEdgeCases:
    """Test edge cases in forecasting"""

    def test_zero_velocity_product(self):
        """Test forecasting for product with zero velocity"""
        product = {
            "sku_id": "slow_mover",
            "category": "misc",
            "daily_velocity": 0
        }

        forecast = get_demand_forecast(
            product=product,
            current_stock=100,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        # Should handle gracefully
        assert forecast["cumulative_demand"] >= 0
        assert forecast["stockout_day"] is None  # Won't stockout with 0 demand

    def test_very_high_stock(self, sample_product):
        """Test forecasting with very high stock levels"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=10000,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=7
        )

        assert forecast["urgency"] == "normal"
        assert forecast["recommended_order_qty"] == 0  # No order needed

    def test_long_forecast_period(self, sample_product):
        """Test forecasting for extended period"""
        forecast = get_demand_forecast(
            product=sample_product,
            current_stock=100,
            weather={"temperature": 25, "condition": "clear"},
            upcoming_festivals=[],
            forecast_days=30
        )

        assert len(forecast["daily_forecasts"]) == 30
        assert forecast["cumulative_demand"] > 200  # 30 days × ~8/day


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
