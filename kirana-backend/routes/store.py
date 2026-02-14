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

        # Return profile
        profile = {
            "store_id": store_data["store_id"],
            "store_name": store_data.get("name", store_data.get("store_name", "")),
            "owner_name": store_data["owner_name"],
            "city": store_data["city"],
            "phone": store_data.get("phone", ""),
            "upi_id": store_data.get("upi_id", ""),
            "language_preference": store_data.get("language", store_data.get("language_preference", "hinglish"))
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

        # Build product list with stock info
        products_list = []
        for product in products_data["products"]:
            sku_id = product["sku_id"]
            inv_data = inventory.get(sku_id, {})

            # Calculate days of stock
            current_stock = inv_data.get("current_stock", 0)
            daily_sales = product.get("typical_daily_sales", 1.0)
            days_of_stock = current_stock / daily_sales if daily_sales > 0 else 0

            # Determine status
            if days_of_stock < 1.0:
                status = "critical"
            elif days_of_stock < 3.0:
                status = "warning"
            else:
                status = "healthy"

            products_list.append({
                "sku_id": sku_id,
                "name": product["name"],
                "name_hi": product.get("name_hi", ""),
                "current_stock": current_stock,
                "days_of_stock": round(days_of_stock, 1),
                "status": status,
                "mrp": product["mrp"],
                "category": product.get("category", "")
            })

        # Sort by days of stock (ascending)
        products_list.sort(key=lambda p: p["days_of_stock"])

        return {
            "store_id": store_id,
            "total_products": len(products_list),
            "low_stock_count": len(low_stock),
            "products": products_list,
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

        # Get daily summary
        summary = engine.get_daily_summary()

        # Get udhaar info
        udhaar_customers = store_data.get("udhaar_customers", [])
        udhaar_total = sum(customer.get("outstanding_amount", 0) for customer in udhaar_customers)

        return {
            "store_id": store_id,
            "daily_summary": summary,
            "udhaar_outstanding": udhaar_total,
            "udhaar_customers": udhaar_customers,
            "last_updated": datetime.now().isoformat()
        }

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

        return {
            "store_id": store_id,
            "forecast_days": days,
            "forecasts": forecasts,
            "context": {
                "upcoming_festivals": [
                    {
                        "name": f["name"],
                        "days_until": f["days_until"]
                    }
                    for f in festivals[:3]  # Top 3 upcoming
                ],
                "weather": {
                    "temp_c": weather.get("temp_c"),
                    "condition": weather.get("condition")
                }
            },
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
