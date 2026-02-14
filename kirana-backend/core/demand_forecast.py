"""
Demand Forecasting Engine
Predicts demand using festival, weather, and day-of-week multipliers
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from config.constants import (
    FESTIVAL_MULTIPLIERS,
    get_weather_multiplier,
    get_dow_multiplier
)


def get_demand_forecast(
    product: Dict,
    days: int,
    context: Dict
) -> Dict:
    """
    Calculate demand forecast for a product

    Args:
        product: Product data with current_stock, avg_daily_sales, category
        days: Number of days to forecast
        context: {
            "upcoming_festivals": List of festivals,
            "weather": Weather data,
            "current_date": Current date
        }

    Returns:
        Forecast with predicted demand, days of stock, recommended order
    """
    product_id = product.get("sku_id") or product.get("product_id")
    category = product.get("category", "")
    base_velocity = product.get("avg_daily_sales") or product.get("typical_daily_sales", 1)
    current_stock = product.get("current_stock", 0)

    # Get context data
    upcoming_festivals = context.get("upcoming_festivals", [])
    weather = context.get("weather", {})
    current_date = context.get("current_date", datetime.now())

    # Calculate daily forecasts
    daily_forecasts = []
    cumulative_demand = 0
    remaining_stock = current_stock

    for day_offset in range(days):
        forecast_date = current_date + timedelta(days=day_offset)
        day_name = forecast_date.strftime("%A")

        # 1. Base velocity
        daily_demand = base_velocity

        # 2. Festival multiplier
        festival_mult = 1.0
        active_festival = None
        for festival in upcoming_festivals:
            # Check if this day falls within festival period
            fest_start = datetime.fromisoformat(festival.get("starts", festival.get("start_date", "")))
            fest_duration = festival.get("duration_days", 1)
            fest_end = fest_start + timedelta(days=fest_duration)

            if fest_start.date() <= forecast_date.date() <= fest_end.date():
                # Check if product category is affected
                fest_id = festival.get("id", "")
                fest_multipliers = FESTIVAL_MULTIPLIERS.get(fest_id, {})

                if category in fest_multipliers:
                    mult = fest_multipliers[category]
                    if mult > festival_mult:
                        festival_mult = mult
                        active_festival = festival.get("name", fest_id)

        daily_demand *= festival_mult

        # 3. Weather multiplier (use current weather for simplicity)
        temp_c = weather.get("temp_c", 25)
        condition = weather.get("condition", "clear")
        weather_mult = get_weather_multiplier(category, temp_c, condition)
        daily_demand *= weather_mult

        # 4. Day of week multiplier
        dow_mult = get_dow_multiplier(category, day_name)
        daily_demand *= dow_mult

        # Round to reasonable value
        daily_demand = round(daily_demand, 1)
        cumulative_demand += daily_demand
        remaining_stock -= daily_demand

        # Create daily forecast entry
        forecast_entry = {
            "date": forecast_date.date().isoformat(),
            "day_of_week": day_name,
            "demand": daily_demand,
            "stock_before": round(remaining_stock + daily_demand, 1),
            "stock_after": round(remaining_stock, 1),
            "factors": {
                "base": base_velocity,
                "festival": f"{festival_mult}x",
                "weather": f"{weather_mult}x",
                "day_of_week": f"{dow_mult}x"
            }
        }

        if active_festival:
            forecast_entry["festival"] = active_festival

        if remaining_stock < 0:
            forecast_entry["stockout"] = True
            forecast_entry["stockout_by"] = abs(round(remaining_stock, 1))

        daily_forecasts.append(forecast_entry)

    # Calculate overall metrics
    avg_daily_demand = cumulative_demand / days if days > 0 else base_velocity
    days_of_stock_normal = current_stock / base_velocity if base_velocity > 0 else 999
    days_of_stock_forecast = current_stock / avg_daily_demand if avg_daily_demand > 0 else 999

    # Find first stockout day
    stockout_day = None
    for i, forecast in enumerate(daily_forecasts):
        if forecast.get("stockout"):
            stockout_day = i + 1
            break

    # Recommended order quantity
    # Order enough for forecast period + buffer
    buffer_days = 3
    total_needed = cumulative_demand + (avg_daily_demand * buffer_days)
    recommended_order = max(0, round(total_needed - current_stock))

    # Determine urgency
    if days_of_stock_forecast < 1.0:
        urgency = "critical"
    elif days_of_stock_forecast < 2.0:
        urgency = "high"
    elif days_of_stock_forecast < 3.0:
        urgency = "medium"
    else:
        urgency = "low"

    logger.info(
        f"Forecast for {product_id}: "
        f"{days_of_stock_forecast:.1f} days stock, "
        f"recommend ordering {recommended_order}"
    )

    return {
        "product_id": product_id,
        "product_name": product.get("name", product_id),
        "category": category,
        "current_stock": current_stock,
        "base_daily_sales": base_velocity,
        "avg_forecast_demand": round(avg_daily_demand, 1),
        "days_of_stock_normal": round(days_of_stock_normal, 1),
        "days_of_stock_forecast": round(days_of_stock_forecast, 1),
        "cumulative_demand": round(cumulative_demand, 1),
        "recommended_order_qty": recommended_order,
        "urgency": urgency,
        "stockout_day": stockout_day,
        "daily_forecasts": daily_forecasts,
        "has_festival_impact": any(f.get("festival") for f in daily_forecasts)
    }


def get_bulk_forecast(
    products: List[Dict],
    days: int,
    context: Dict,
    filter_low_stock: bool = True
) -> List[Dict]:
    """
    Get forecast for multiple products

    Args:
        products: List of product data
        days: Forecast period
        context: Forecast context
        filter_low_stock: Only return items needing reorder

    Returns:
        List of forecasts, sorted by urgency
    """
    forecasts = []

    for product in products:
        try:
            forecast = get_demand_forecast(product, days, context)
            forecasts.append(forecast)
        except Exception as e:
            product_id = product.get("sku_id") or product.get("product_id", "unknown")
            logger.error(f"Forecast failed for {product_id}: {e}")

    # Filter if requested
    if filter_low_stock:
        forecasts = [
            f for f in forecasts
            if f["urgency"] in ["critical", "high"] or f["recommended_order_qty"] > 0
        ]

    # Sort by urgency and days of stock
    urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    forecasts.sort(
        key=lambda x: (
            urgency_order.get(x["urgency"], 3),
            x["days_of_stock_forecast"]
        )
    )

    logger.info(f"Bulk forecast: {len(forecasts)} products analyzed")
    return forecasts
