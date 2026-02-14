"""
Procurement Engine
Generates optimized procurement orders based on demand forecasts and pricing
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from loguru import logger
from core.demand_forecast import get_bulk_forecast
from core.price_comparison import optimize_order_split


def generate_procurement_order(
    products: List[Dict],
    distributors: List[Dict],
    context: Dict,
    store_id: str,
    forecast_days: int = 7
) -> Dict:
    """
    Generate optimized procurement order

    Args:
        products: Product catalog with current inventory
        distributors: Available distributors
        context: Forecast context (festivals, weather, date)
        store_id: Store identifier
        forecast_days: Days to forecast ahead

    Returns:
        Complete procurement order with optimization
    """
    logger.info(f"Generating procurement order for {store_id}")

    # 1. Get demand forecasts for all products
    forecasts = get_bulk_forecast(
        products=products,
        days=forecast_days,
        context=context,
        filter_low_stock=True  # Only items needing reorder
    )

    if not forecasts:
        logger.info("No items need reordering")
        return {
            "order_id": None,
            "items": [],
            "message": "All items have sufficient stock"
        }

    # 2. Build order items from forecasts
    order_items = []
    for forecast in forecasts:
        if forecast["recommended_order_qty"] > 0:
            order_items.append({
                "product_id": forecast["product_id"],
                "product_name": forecast["product_name"],
                "quantity": forecast["recommended_order_qty"],
                "urgency": forecast["urgency"],
                "reason": _get_order_reason(forecast),
                "current_stock": forecast["current_stock"],
                "days_of_stock": forecast["days_of_stock_forecast"],
                "forecast_demand": forecast["avg_forecast_demand"],
                "category": forecast.get("category", "")
            })

    if not order_items:
        logger.info("No items above threshold for ordering")
        return {
            "order_id": None,
            "items": [],
            "message": "Stock levels acceptable"
        }

    # 3. Optimize order across distributors
    optimization = optimize_order_split(order_items, distributors)

    # 4. Enrich with product details and distributor info
    enriched_items = []
    for item in optimization["optimized_items"]:
        product = next((p for p in products if p.get("sku_id") == item["product_id"]), None)

        if not product:
            continue

        mrp = product.get("mrp", item["unit_price"] * 1.2)
        savings_per_unit = mrp - item["unit_price"]

        enriched_item = {
            "product_id": item["product_id"],
            "name": item.get("product_name", product.get("name", "")),
            "name_local": product.get("name_hi", ""),
            "quantity": item["quantity"],
            "unit": product.get("unit", "packets"),
            "best_distributor": item["distributor_name"],
            "distributor_id": item["distributor_id"],
            "unit_price": item["unit_price"],
            "total_price": item["total_price"],
            "mrp": mrp,
            "savings_per_unit": round(savings_per_unit, 2),
            "urgency": item.get("urgency", "medium"),
            "reason": item.get("reason", "Reorder needed"),
            "days_of_stock": item.get("days_of_stock", 0),
            "recommended_by": _get_recommendation_source(item)
        }

        enriched_items.append(enriched_item)

    # 5. Build distributor split with contact info
    distributor_split = []
    for split in optimization["distributor_split"]:
        dist = next((d for d in distributors if d["id"] == split["distributor_id"]), None)
        if dist:
            distributor_split.append({
                "distributor_id": split["distributor_id"],
                "name": split["distributor_name"],
                "items_count": len(split["items"]),
                "total_amount": round(split["total_amount"], 2),
                "delivery_days": dist.get("delivery_days", 1),
                "contact": dist.get("phone", ""),
                "upi_id": dist.get("upi_id", "")
            })

    # 6. Generate UPI deep links
    upi_deeplinks = []
    for split in distributor_split:
        if split.get("upi_id"):
            upi_link = (
                f"upi://pay?"
                f"pa={split['upi_id']}&"
                f"pn={split['name']}&"
                f"am={split['total_amount']}&"
                f"tn=Procurement Order"
            )
            upi_deeplinks.append({
                "distributor": split["name"],
                "distributor_id": split["distributor_id"],
                "amount": split["total_amount"],
                "upi_link": upi_link
            })

    # 7. Calculate summary
    total_quantity = sum(item["quantity"] for item in enriched_items)
    total_cost = optimization["total_cost"]
    total_mrp = sum(item["mrp"] * item["quantity"] for item in enriched_items)
    total_savings = total_mrp - total_cost
    savings_pct = (total_savings / total_mrp * 100) if total_mrp > 0 else 0

    summary = {
        "total_items": len(enriched_items),
        "total_quantity": total_quantity,
        "total_cost": round(total_cost, 2),
        "total_mrp_value": round(total_mrp, 2),
        "total_savings": round(total_savings, 2),
        "savings_percentage": round(savings_pct, 1)
    }

    # 8. Festival context (if applicable)
    festival_context = None
    upcoming_festivals = context.get("upcoming_festivals", [])
    if upcoming_festivals:
        fest = upcoming_festivals[0]
        festival_context = {
            "name": fest.get("name", ""),
            "starts": fest.get("starts") or fest.get("start_date", ""),
            "impact": fest.get("impact_level", ""),
            "affected_categories": list(set(item["category"] for item in order_items if item.get("category")))
        }

    # 9. Build final order
    order_id = f"ord_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    order = {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(),
        "store_id": store_id,
        "items": enriched_items,
        "summary": summary,
        "savings_vs_default": {
            "amount": round(optimization["savings_vs_single"], 2),
            "explanation": f"Split order across {len(distributor_split)} distributors saves ₹{optimization['savings_vs_single']:.2f} vs single distributor"
        },
        "distributor_split": distributor_split,
        "upi_deeplinks": upi_deeplinks,
        "valid_until": (datetime.now() + timedelta(hours=24)).isoformat(),
        "festival_context": festival_context
    }

    logger.info(
        f"Order generated: {len(enriched_items)} items, "
        f"₹{total_cost:.2f} total, "
        f"{len(distributor_split)} distributors"
    )

    return order


def _get_order_reason(forecast: Dict) -> str:
    """Generate human-readable order reason"""
    urgency = forecast["urgency"]
    current_stock = forecast["current_stock"]
    days_of_stock = forecast["days_of_stock_forecast"]
    has_festival = forecast.get("has_festival_impact", False)

    if urgency == "critical":
        return f"Only {current_stock} left, critically low stock (less than {days_of_stock:.1f} days)"
    elif has_festival and days_of_stock < 3:
        return f"Festival coming, current stock only covers {days_of_stock:.1f} days at festival demand"
    elif urgency == "high":
        return f"Running low - {days_of_stock:.1f} days remaining"
    else:
        return f"Reorder point reached"


def _get_recommendation_source(item: Dict) -> str:
    """Determine what triggered the recommendation"""
    urgency = item.get("urgency", "")
    days_of_stock = item.get("days_of_stock", 0)

    if urgency == "critical":
        return "inventory_alert"
    elif days_of_stock < 3:
        return "demand_forecast"
    else:
        return "routine_reorder"
