"""
Procurement-related Pydantic models
Defines ProcurementOrder, ProcurementItem, and order optimization models
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict
from datetime import datetime


class ProcurementItem(BaseModel):
    """Single item in a procurement order"""
    product_id: str = Field(..., description="Product SKU ID")
    name: str = Field(..., description="Product name in English")
    name_local: str = Field(..., description="Product name in Hindi/local language")
    quantity: int = Field(..., gt=0, description="Quantity to order")
    unit: str = Field(..., description="Unit (packets, kg, liters, pieces)")
    best_distributor: str = Field(..., description="Selected distributor name")
    distributor_id: str = Field(..., description="Distributor ID")
    unit_price: float = Field(..., gt=0.0, description="Price per unit")
    total_price: float = Field(..., gt=0.0, description="Total cost for this item")
    mrp: float = Field(..., gt=0.0, description="MRP for reference")
    savings_per_unit: float = Field(..., ge=0.0, description="Savings vs MRP")
    urgency: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Order urgency"
    )
    reason: str = Field(..., description="Reason for ordering this item")
    days_of_stock: float = Field(..., ge=0.0, description="Current days of stock")
    days_of_stock_festival: Optional[float] = Field(
        None,
        description="Days of stock considering festival demand"
    )
    recommended_by: Literal["inventory_alert", "demand_forecast", "festival_forecast"] = Field(
        ...,
        description="What triggered this recommendation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "maggi_70g",
                "name": "Maggi 2-Minute Noodles 70g",
                "name_local": "मैगी नूडल्स",
                "quantity": 25,
                "unit": "packets",
                "best_distributor": "Patel Wholesale",
                "distributor_id": "patel_wholesale",
                "unit_price": 11.5,
                "total_price": 287.5,
                "mrp": 14.0,
                "savings_per_unit": 2.5,
                "urgency": "critical",
                "reason": "Only 3 packets left, critically low stock",
                "days_of_stock": 0.375,
                "recommended_by": "inventory_alert"
            }
        }


class DistributorSplit(BaseModel):
    """Order split per distributor"""
    distributor_id: str = Field(...)
    name: str = Field(..., description="Distributor name")
    items_count: int = Field(..., gt=0, description="Number of items from this distributor")
    total_amount: float = Field(..., gt=0.0, description="Total cost for this distributor")
    delivery_days: int = Field(..., ge=0, description="Expected delivery time")
    contact: str = Field(..., description="Contact phone number")


class UPIDeeplink(BaseModel):
    """UPI payment deep link"""
    distributor: str = Field(..., description="Distributor name")
    distributor_id: str = Field(..., description="Distributor ID")
    amount: float = Field(..., gt=0.0, description="Payment amount")
    upi_link: str = Field(..., description="UPI deep link URL")
    qr_code_url: Optional[str] = Field(None, description="QR code image URL")


class OrderSummary(BaseModel):
    """Order summary and totals"""
    total_items: int = Field(..., gt=0, description="Total unique items")
    total_quantity: int = Field(..., gt=0, description="Total quantity across all items")
    total_cost: float = Field(..., gt=0.0, description="Total order cost")
    total_mrp_value: float = Field(..., gt=0.0, description="Total MRP value")
    total_savings: float = Field(..., ge=0.0, description="Total savings vs MRP")
    savings_percentage: float = Field(..., ge=0.0, description="Savings percentage")


class SavingsBreakdown(BaseModel):
    """Savings breakdown"""
    amount: float = Field(..., ge=0.0, description="Additional savings amount")
    explanation: str = Field(..., description="How savings were achieved")


class FestivalContext(BaseModel):
    """Festival context for the order"""
    name: str = Field(..., description="Festival name")
    starts: str = Field(..., description="Festival start date")
    impact: str = Field(..., description="Impact level")
    affected_categories: List[str] = Field(..., description="Categories affected")


class ProcurementOrder(BaseModel):
    """Complete procurement order with optimization"""
    order_id: str = Field(..., description="Unique order identifier")
    created_at: str = Field(..., description="ISO timestamp")
    store_id: str = Field(..., description="Store identifier")

    items: List[ProcurementItem] = Field(..., description="Items to order")
    summary: OrderSummary = Field(..., description="Order summary")
    savings_vs_default: SavingsBreakdown = Field(
        ...,
        description="Savings from multi-distributor optimization"
    )
    distributor_split: List[DistributorSplit] = Field(
        ...,
        description="How order is split across distributors"
    )
    upi_deeplinks: List[UPIDeeplink] = Field(
        ...,
        description="UPI payment links per distributor"
    )
    valid_until: str = Field(..., description="Order validity timestamp")
    festival_context: Optional[FestivalContext] = Field(
        None,
        description="Festival context if applicable"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord_20260214_001",
                "created_at": "2026-02-14T14:30:00Z",
                "store_id": "sharma_general_store",
                "items": [],
                "summary": {
                    "total_items": 12,
                    "total_quantity": 125,
                    "total_cost": 3847.50,
                    "total_mrp_value": 4850.00,
                    "total_savings": 1002.50,
                    "savings_percentage": 20.7
                }
            }
        }


class PriceComparison(BaseModel):
    """Price comparison result for a product"""
    product_id: str = Field(...)
    distributors: Dict[str, float] = Field(..., description="Distributor to price mapping")
    cheapest: str = Field(..., description="Cheapest distributor")
    cheapest_price: float = Field(..., gt=0.0)
    most_expensive: str = Field(...)
    most_expensive_price: float = Field(..., gt=0.0)
    savings: float = Field(..., ge=0.0, description="Savings by choosing cheapest")
