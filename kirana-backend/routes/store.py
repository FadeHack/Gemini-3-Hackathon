"""
Store API routes
Provides store profile, inventory, P&L, and forecast data
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime
import json

from config.settings import settings
from core.inventory_engine import InventoryEngine
from core.demand_forecast import get_bulk_forecast
from core.festival_calendar import get_upcoming_festivals
from services.weather_service import get_weather_service
from utils.validators import validate_store_id
from utils.formatters import format_currency, create_summary_message

router = APIRouter(prefix="/api/store", tags=["store"])


@router.get("/{store_id}/profile")
async def get_store_profile(store_id: str):
    """
    Get store profile information

    Returns store details including name, owner, location, and contact info.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Response:**
    ```json
    {
      "store_id": "sharma_general_store",
      "store_name": "Sharma General Store",
      "owner_name": "Rajesh Sharma",
      "city": "Indore",
      "phone": "+91 98765 43210",
      "upi_id": "rajesh@paytm"
    }
    ```
    """
    try:
        # Validate store_id
        is_valid, error = validate_store_id(store_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Load store data
        store_path = settings.get_store_path(store_id)
        with open(store_path, "r") as f:
            store_data = json.load(f)

        # Load product catalog for inventory summary
        with open(settings.PRODUCT_CATALOG_PATH, "r") as f:
            products_data = json.load(f)

        # Get inventory summary
        inventory = store_data["current_inventory"]
        metadata = store_data.get("metadata", {})

        # Return enhanced profile with frontend-compatible fields
        profile = {
            "store_id": store_data["store_id"],
            "store_name": store_data.get("name", store_data.get("store_name", "")),
            "name": store_data.get("name", store_data.get("store_name", "")),  # Frontend field
            "owner_name": store_data["owner_name"],
            "city": store_data["city"],
            "state": store_data.get("state", ""),  # Frontend field
            "phone": store_data.get("phone", ""),
            "upi_id": store_data.get("upi_id", ""),
            "language_preference": store_data.get("language", store_data.get("language_preference", "hinglish")),
            "language": store_data.get("language", store_data.get("language_preference", "hinglish")),  # Frontend field
            "products": products_data["products"],  # Frontend field - full product catalog
            "inventory_summary": {  # Frontend field
                "total_products": metadata.get("total_products", len(inventory)),
                "critical_stock": metadata.get("critical_stock_count", 0),
                "warning_stock": metadata.get("warning_stock_count", 0),
                "healthy_stock": metadata.get("healthy_stock_count", 0)
            }
        }

        return profile

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Store not found: {store_id}"
        )
    except Exception as e:
        logger.error(f"Error getting store profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{store_id}/inventory")
async def get_store_inventory(store_id: str):
    """
    Get current inventory status

    Returns all products with current stock levels, days of stock, and alerts.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Response:**
    ```json
    {
      "store_id": "sharma_general_store",
      "total_products": 20,
      "low_stock_count": 4,
      "products": [
        {
          "sku_id": "maggi_70g",
          "name": "Maggi 2-Minute Noodles",
          "current_stock": 3,
          "days_of_stock": 0.6,
          "status": "critical",
          "mrp": 14.0
        }
      ],
      "alerts": [...],
      "last_updated": "2026-02-14T12:00:00Z"
    }
    ```
    """
    try:
        # Validate store_id
        is_valid, error = validate_store_id(store_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Load store data
        store_path = settings.get_store_path(store_id)
        with open(store_path, "r") as f:
            store_data = json.load(f)

        # Load product catalog
        with open(settings.PRODUCT_CATALOG_PATH, "r") as f:
            products_data = json.load(f)

        # Initialize inventory engine
        inventory = store_data["current_inventory"]
        engine = InventoryEngine(store_id, inventory)

        # Get low stock items
        low_stock = engine.get_low_stock_items(threshold_days=3.0)

        # Build inventory object (frontend expects keyed object, not array)
        inventory_obj = {}
        products_list = []  # Keep for backward compatibility

        for product in products_data["products"]:
            sku_id = product["sku_id"]
            inv_data = inventory.get(sku_id, {})

            # Calculate days of stock
            current_stock = inv_data.get("current_stock", 0)
            daily_sales = product.get("typical_daily_sales", 1.0)
            avg_daily_velocity = inv_data.get("avg_daily_sales", daily_sales)
            days_of_stock = current_stock / avg_daily_velocity if avg_daily_velocity > 0 else 0

            # Determine status
            if days_of_stock < 1.0:
                status = "critical"
            elif days_of_stock < 3.0:
                status = "warning"
            else:
                status = "healthy"

            # Frontend-compatible structure
            inventory_item = {
                "current_stock": current_stock,
                "today_sold": inv_data.get("today_sold", 0),  # Frontend field
                "today_received": inv_data.get("today_received", 0),  # Frontend field
                "avg_daily_velocity": avg_daily_velocity,  # Frontend field name
                "days_of_stock": round(days_of_stock, 1),
                "status": status
            }

            inventory_obj[sku_id] = inventory_item

            # Also build array for backward compatibility
            products_list.append({
                "sku_id": sku_id,
                "name": product["name"],
                "name_hi": product.get("name_hi", ""),
                "current_stock": current_stock,
                "today_sold": inv_data.get("today_sold", 0),
                "today_received": inv_data.get("today_received", 0),
                "avg_daily_sales": avg_daily_velocity,
                "days_of_stock": round(days_of_stock, 1),
                "reorder_point": product.get("reorder_point", 10),
                "price": product["mrp"],
                "status": status,
                "status_message": f"{'🔴 Critically low' if status == 'critical' else '🟡 Warning' if status == 'warning' else '🟢 Stock OK'}",
                "category": product.get("category", "")
            })

        # Sort by days of stock (ascending)
        products_list.sort(key=lambda p: p["days_of_stock"])

        return {
            "store_id": store_id,
            "total_products": len(products_list),
            "low_stock_count": len(low_stock),
            "critical_stock_count": sum(1 for p in products_list if p["status"] == "critical"),
            "inventory": inventory_obj,  # Frontend expects this
            "products": products_list,  # Backward compatibility
            "alerts": low_stock,
            "last_updated": datetime.now().isoformat()
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Store not found: {store_id}"
        )
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{store_id}/pnl")
async def get_store_pnl(store_id: str):
    """
    Get Profit & Loss summary

    Returns daily sales summary with payment breakdown and udhaar outstanding.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Response:**
    ```json
    {
      "store_id": "sharma_general_store",
      "daily_summary": {
        "total_revenue": 4820.0,
        "items_sold": 45,
        "cash_sales": 2000.0,
        "upi_sales": 2320.0,
        "credit_sales": 500.0
      },
      "udhaar_outstanding": 8740.0,
      "udhaar_customers": [...]
    }
    ```
    """
    try:
        # Validate store_id
        is_valid, error = validate_store_id(store_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Load store data
        store_path = settings.get_store_path(store_id)
        with open(store_path, "r") as f:
            store_data = json.load(f)

        # Initialize inventory engine
        inventory = store_data["current_inventory"]
        engine = InventoryEngine(store_id, inventory)

        # Get daily summary from store data
        daily_summary = store_data.get("daily_summary", {})

        # Calculate P&L metrics
        total_revenue = daily_summary.get("total_revenue", 0)
        items_sold = daily_summary.get("items_sold", 0)

        # Estimate COGS (typically 60-70% of revenue for kirana)
        total_cogs = total_revenue * 0.65
        gross_profit = total_revenue - total_cogs
        margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Get payment breakdown
        cash_collected = daily_summary.get("cash_collected", 0)
        upi_collected = daily_summary.get("upi_collected", 0)
        credit_given = daily_summary.get("credit_given", 0)
        total_transactions = daily_summary.get("total_transactions", 0)

        # Frontend-compatible flat structure
        pnl_response = {
            "date": daily_summary.get("date", datetime.now().strftime("%Y-%m-%d")),
            "total_revenue": total_revenue,
            "total_cogs": round(total_cogs, 2),  # Frontend field
            "gross_profit": round(gross_profit, 2),  # Frontend field
            "margin_pct": round(margin_pct, 1),  # Frontend field
            "cash_collected": cash_collected,  # Frontend field name
            "upi_collected": upi_collected,  # Frontend field name
            "credit_given": credit_given,  # Frontend field name
            "total_transactions": total_transactions,
            "items_sold": items_sold  # Frontend field
        }

        # Also include backward-compatible structure
        pnl_response["store_id"] = store_id
        pnl_response["period_days"] = 1
        pnl_response["summary"] = {
            "total_revenue": total_revenue,
            "total_transactions": total_transactions,
            "avg_transaction_value": total_revenue / total_transactions if total_transactions > 0 else 0,
            "cash_sales": cash_collected,
            "upi_sales": upi_collected,
            "credit_sales": credit_given,
            "outstanding_credit": 0  # Will be in /udhaar endpoint
        }
        pnl_response["daily_breakdown"] = []
        pnl_response["timestamp"] = datetime.now().isoformat()

        return pnl_response

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Store not found: {store_id}"
        )
    except Exception as e:
        logger.error(f"Error getting P&L: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{store_id}/udhaar")
async def get_udhaar_ledger(store_id: str):
    """
    Get Udhaar (Credit) Ledger

    Returns all customers with outstanding credit and transaction history.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Response:**
    ```json
    {
      "total_outstanding": 8740.0,
      "customers": [
        {
          "name": "Sharma ji",
          "amount": 2340.0,
          "last_transaction": "2026-02-14",
          "transactions_count": 5
        }
      ]
    }
    ```
    """
    try:
        # Validate store_id
        is_valid, error = validate_store_id(store_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Load store data
        store_path = settings.get_store_path(store_id)
        with open(store_path, "r") as f:
            store_data = json.load(f)

        # Get udhaar ledger
        udhaar_ledger = store_data.get("udhaar_ledger", {})

        # Transform to frontend-compatible format
        customers = []
        total_outstanding = 0

        for customer_name, customer_data in udhaar_ledger.items():
            amount = customer_data.get("total_outstanding", 0)
            total_outstanding += amount

            customers.append({
                "name": customer_name,
                "amount": amount,
                "last_transaction": customer_data.get("last_transaction_date", ""),
                "transactions_count": customer_data.get("transactions_count", 0)
            })

        # Sort by amount (descending)
        customers.sort(key=lambda c: c["amount"], reverse=True)

        return {
            "total_outstanding": total_outstanding,
            "customers": customers
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Store not found: {store_id}"
        )
    except Exception as e:
        logger.error(f"Error getting udhaar ledger: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{store_id}/forecast")
async def get_demand_forecast(
    store_id: str,
    days: int = 7
):
    """
    Get demand forecast for all products

    Provides 7-day demand forecast considering festivals, weather, and day-of-week patterns.

    **Path Parameters:**
    - `store_id`: Store identifier

    **Query Parameters:**
    - `days`: Forecast horizon in days (default: 7, max: 30)

    **Response:**
    ```json
    {
      "store_id": "sharma_general_store",
      "forecast_days": 7,
      "forecasts": [
        {
          "product_id": "maggi_70g",
          "product_name": "Maggi 2-Minute Noodles",
          "days_of_stock_forecast": 0.6,
          "recommended_order_qty": 48,
          "urgency": "critical",
          "has_festival_impact": false
        }
      ],
      "context": {
        "upcoming_festivals": [...],
        "weather": {...}
      }
    }
    ```
    """
    try:
        # Validate store_id
        is_valid, error = validate_store_id(store_id)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        # Validate days parameter
        if days < 1 or days > 30:
            raise HTTPException(
                status_code=400,
                detail="days must be between 1 and 30"
            )

        # Load store data
        store_path = settings.get_store_path(store_id)
        with open(store_path, "r") as f:
            store_data = json.load(f)

        # Load product catalog
        with open(settings.PRODUCT_CATALOG_PATH, "r") as f:
            products_data = json.load(f)

        # Get weather context
        weather_service = get_weather_service()
        city = store_data.get("city", "Indore")
        weather = await weather_service.get_current_weather(city)

        # Get upcoming festivals
        festivals = get_upcoming_festivals(days_ahead=days)

        # Build context
        context = {
            "upcoming_festivals": festivals,
            "weather": weather,
            "current_date": datetime.now()
        }

        # Add current stock to products
        inventory = store_data["current_inventory"]
        products_with_stock = []
        for product in products_data["products"]:
            product_copy = {**product}
            inv_data = inventory.get(product["sku_id"], {})
            product_copy["current_stock"] = inv_data.get("current_stock", 0)
            products_with_stock.append(product_copy)

        # Get bulk forecast
        forecasts = get_bulk_forecast(
            products_with_stock,
            days=days,
            context=context
        )

        # Transform forecasts to frontend-compatible structure
        frontend_forecasts = []
        for forecast in forecasts:
            # Map daily_forecasts to daily_demand for frontend
            daily_demand = []
            for daily in forecast.get("daily_forecasts", []):
                demand_entry = {
                    "date": daily["date"],
                    "demand": daily["demand"],
                    "stock": daily["stock_after"]  # Frontend uses "stock" field
                }
                # Add festival if present
                if "festival" in daily:
                    demand_entry["festival"] = daily["festival"]
                daily_demand.append(demand_entry)

            # Create frontend-compatible forecast object
            frontend_forecast = {
                "product_id": forecast["product_id"],
                "product_name": forecast["product_name"],
                "category": forecast["category"],
                "current_stock": forecast["current_stock"],
                "base_daily_sales": forecast["base_daily_sales"],
                "avg_forecast_demand": forecast["avg_forecast_demand"],
                "days_of_stock_forecast": forecast["days_of_stock_forecast"],
                "recommended_order_qty": forecast["recommended_order_qty"],
                "recommended_order": forecast["recommended_order_qty"],  # Frontend alias
                "urgency": forecast["urgency"],
                "stockout_day": forecast.get("stockout_day"),
                "has_festival_impact": forecast["has_festival_impact"],
                "daily_demand": daily_demand,  # Frontend expects this field
                "daily_forecasts": forecast.get("daily_forecasts", []),  # Keep for backward compatibility
                "reorder_point": forecast.get("reorder_point", 10)  # Frontend field
            }
            frontend_forecasts.append(frontend_forecast)

        # Also return as "products" for frontend compatibility
        products_forecast = []
        for forecast in frontend_forecasts:
            products_forecast.append({
                "product_id": forecast["product_id"],
                "daily_demand": forecast["daily_demand"],
                "reorder_point": forecast["reorder_point"],
                "recommended_order": forecast["recommended_order"]
            })

        return {
            "store_id": store_id,
            "forecast_days": days,
            "forecasts": frontend_forecasts,  # Full structure
            "products": products_forecast,  # Frontend-simplified structure
            "upcoming_festivals": [
                {
                    "name": f["name"],
                    "starts": f.get("start_date", f.get("starts", "")),
                    "days_until": f["days_until"],
                    "duration_days": f.get("duration_days", 1),
                    "impact": f.get("impact", "medium")
                }
                for f in festivals[:3]  # Top 3 upcoming
            ],
            "context": {
                "upcoming_festivals": [
                    {
                        "name": f["name"],
                        "days_until": f["days_until"]
                    }
                    for f in festivals[:3]
                ],
                "weather": {
                    "temp_c": weather.get("temp_c"),
                    "condition": weather.get("condition")
                }
            },
            "timestamp": datetime.now().isoformat(),
            "generated_at": datetime.now().isoformat()
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Store not found: {store_id}"
        )
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
