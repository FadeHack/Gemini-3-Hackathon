"""
Price Comparison Engine
Compares prices across distributors and finds best deals
"""

from typing import Dict, List, Tuple, Optional
from loguru import logger


def compare_distributors(
    product_id: str,
    distributors: List[Dict]
) -> Optional[Dict]:
    """
    Compare prices for a product across all distributors

    Args:
        product_id: Product SKU ID
        distributors: List of distributor profiles with pricing

    Returns:
        Price comparison result or None if product not available
    """
    prices = {}

    for dist in distributors:
        dist_products = dist.get("products", {})
        if product_id in dist_products:
            price_info = dist_products[product_id]
            # Handle both dict format {"price": X, "moq": Y} and simple number format
            if isinstance(price_info, dict):
                unit_price = price_info.get("price", 0)
                moq = price_info.get("moq", 1)
            else:
                unit_price = price_info
                moq = 1

            prices[dist["id"]] = {
                "distributor_id": dist["id"],
                "distributor_name": dist["name"],
                "price": unit_price,
                "moq": moq,
                "delivery_days": dist.get("delivery_days", 1),
                "minimum_order": dist.get("minimum_order", 0),
                "reliability_score": dist.get("reliability_score", 3.0)
            }

    if not prices:
        logger.warning(f"Product {product_id} not available from any distributor")
        return None

    # Find cheapest and most expensive
    sorted_prices = sorted(prices.items(), key=lambda x: x[1]["price"])
    cheapest_id, cheapest = sorted_prices[0]
    most_expensive_id, most_expensive = sorted_prices[-1]

    savings = most_expensive["price"] - cheapest["price"]
    savings_pct = (savings / most_expensive["price"] * 100) if most_expensive["price"] > 0 else 0

    return {
        "product_id": product_id,
        "available_from": len(prices),
        "prices": prices,
        "cheapest": {
            "distributor_id": cheapest_id,
            "distributor_name": cheapest["distributor_name"],
            "price": cheapest["price"],
            "delivery_days": cheapest["delivery_days"]
        },
        "most_expensive": {
            "distributor_id": most_expensive_id,
            "distributor_name": most_expensive["distributor_name"],
            "price": most_expensive["price"]
        },
        "savings": round(savings, 2),
        "savings_pct": round(savings_pct, 1)
    }


def find_cheapest_distributor(
    product_id: str,
    distributors: List[Dict]
) -> Optional[Tuple[str, str, float]]:
    """
    Find the cheapest distributor for a product

    Args:
        product_id: Product SKU ID
        distributors: List of distributors

    Returns:
        (distributor_id, distributor_name, price) or None
    """
    comparison = compare_distributors(product_id, distributors)
    if not comparison:
        return None

    cheapest = comparison["cheapest"]
    return (
        cheapest["distributor_id"],
        cheapest["distributor_name"],
        cheapest["price"]
    )


def optimize_order_split(
    items: List[Dict],
    distributors: List[Dict]
) -> Dict:
    """
    Optimize order by splitting across distributors for best prices

    Args:
        items: List of items to order: [{product_id, quantity}, ...]
        distributors: List of distributor profiles

    Returns:
        Optimized order split with savings calculation
    """
    # For each item, find cheapest distributor
    optimized_items = []
    distributor_orders = {}  # {distributor_id: {items, total}}

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]

        # Find cheapest distributor
        result = find_cheapest_distributor(product_id, distributors)

        if not result:
            logger.warning(f"No distributor found for {product_id}")
            continue

        dist_id, dist_name, unit_price = result
        total_price = unit_price * quantity

        optimized_items.append({
            **item,
            "distributor_id": dist_id,
            "distributor_name": dist_name,
            "unit_price": unit_price,
            "total_price": total_price
        })

        # Track per-distributor totals
        if dist_id not in distributor_orders:
            distributor_orders[dist_id] = {
                "distributor_id": dist_id,
                "distributor_name": dist_name,
                "items": [],
                "total_amount": 0.0
            }

        distributor_orders[dist_id]["items"].append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price
        })
        distributor_orders[dist_id]["total_amount"] += total_price

    # Calculate total cost
    total_cost = sum(item["total_price"] for item in optimized_items)

    # Calculate savings vs single distributor
    # (Use first distributor as baseline)
    if distributors and optimized_items:
        baseline_dist_id = distributors[0]["id"]
        baseline_cost = 0.0

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            baseline_products = distributors[0].get("products", {})

            if product_id in baseline_products:
                price_info = baseline_products[product_id]
                # Handle both dict and simple number format
                unit_price = price_info.get("price", 0) if isinstance(price_info, dict) else price_info
                baseline_cost += unit_price * quantity

        savings_vs_baseline = baseline_cost - total_cost
    else:
        savings_vs_baseline = 0.0

    return {
        "optimized_items": optimized_items,
        "distributor_split": list(distributor_orders.values()),
        "total_cost": round(total_cost, 2),
        "total_items": len(optimized_items),
        "distributors_used": len(distributor_orders),
        "savings_vs_single": round(savings_vs_baseline, 2)
    }


def get_price_summary(
    product_id: str,
    distributors: List[Dict]
) -> str:
    """
    Get human-readable price summary

    Args:
        product_id: Product SKU
        distributors: Distributor list

    Returns:
        Summary string
    """
    comparison = compare_distributors(product_id, distributors)

    if not comparison:
        return f"Product {product_id} not available from any distributor"

    cheapest = comparison["cheapest"]
    savings = comparison["savings"]
    savings_pct = comparison["savings_pct"]

    return (
        f"Best price: ₹{cheapest['price']} from {cheapest['distributor_name']} "
        f"(saves ₹{savings}, {savings_pct}% vs highest)"
    )
