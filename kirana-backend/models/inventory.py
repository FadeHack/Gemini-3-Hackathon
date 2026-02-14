"""
Inventory-related Pydantic models
Defines Transaction, InventoryAlert, and inventory state models
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, List
from datetime import datetime


class Transaction(BaseModel):
    """Single inventory transaction"""
    transaction_id: str = Field(..., description="Unique transaction ID")
    product_id: str = Field(..., description="Product SKU ID")
    product_name: str = Field(..., description="Product name")
    quantity_change: int = Field(
        ...,
        description="Quantity change (negative=sold, positive=received)"
    )
    transaction_type: Literal["cash", "upi", "credit", "supplier_delivery"] = Field(
        ...,
        description="Type of transaction"
    )
    customer_name: Optional[str] = Field(
        None,
        description="Customer name (for credit sales)"
    )
    price: Optional[float] = Field(
        None,
        ge=0.0,
        description="Transaction price"
    )
    timestamp: str = Field(..., description="ISO timestamp")
    source: Literal["kacchi_parchi", "voice", "shelf_photo", "manual"] = Field(
        ...,
        description="Source of transaction data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_20260214_001",
                "product_id": "maggi_70g",
                "product_name": "Maggi 2-Minute Noodles 70g",
                "quantity_change": -5,
                "transaction_type": "cash",
                "price": 70.0,
                "timestamp": "2026-02-14T14:30:00Z",
                "source": "kacchi_parchi"
            }
        }


class InventoryAlert(BaseModel):
    """Inventory alert for low stock"""
    product_id: str = Field(..., description="Product SKU ID")
    product_name: str = Field(..., description="Product name")
    product_name_local: str = Field(..., description="Hindi/local name")
    current_stock: int = Field(..., ge=0, description="Current stock level")
    days_remaining: float = Field(..., description="Days until stockout")
    status: Literal["critical", "warning", "ok"] = Field(
        ...,
        description="Alert severity"
    )
    message: str = Field(..., description="Alert message for owner")
    urgency: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Action urgency"
    )
    action_required: bool = Field(..., description="Whether immediate action needed")
    recommended_order_qty: Optional[int] = Field(
        None,
        description="Recommended quantity to order"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "maggi_70g",
                "product_name": "Maggi 2-Minute Noodles 70g",
                "product_name_local": "मैगी नूडल्स",
                "current_stock": 3,
                "days_remaining": 0.375,
                "status": "critical",
                "message": "Maggi critically low - only 3 packets left (less than 1 day stock)",
                "urgency": "critical",
                "action_required": True,
                "recommended_order_qty": 25
            }
        }


class InventoryUpdate(BaseModel):
    """Inventory update event"""
    product_id: str = Field(...)
    product_name: str = Field(...)
    product_name_local: str = Field(...)
    old_stock: int = Field(..., ge=0)
    new_stock: int = Field(..., ge=0)
    change: int = Field(..., description="Stock change (can be negative)")
    change_type: Literal["sold", "received", "calibrated"] = Field(...)
    days_of_stock: float = Field(..., ge=0.0)
    status: Literal["healthy", "warning", "critical"] = Field(...)
    transaction_details: Optional[Dict] = Field(None)
    alerts: List[InventoryAlert] = Field(default_factory=list)
    timestamp: str = Field(...)


class UdhaarUpdate(BaseModel):
    """Credit ledger update"""
    customer: str = Field(..., description="Customer name")
    previous_amount: float = Field(..., ge=0.0)
    new_amount: float = Field(..., ge=0.0)
    change: float = Field(..., description="Amount change")
    change_type: Literal["credit_given", "payment_received"] = Field(...)
    transaction: Dict = Field(...)
    running_total: Dict = Field(..., description="Total udhaar outstanding")
    customer_details: Dict = Field(...)
    timestamp: str = Field(...)


class PNLUpdate(BaseModel):
    """Profit & Loss update"""
    date: str = Field(...)
    summary: Dict = Field(..., description="Revenue, COGS, profit, margin")
    transactions: Dict = Field(..., description="Transaction counts")
    inventory: Dict = Field(..., description="Items sold/received")
    top_sellers: List[Dict] = Field(..., description="Top selling items")
    last_updated: str = Field(...)


class InventoryCalibration(BaseModel):
    """Shelf photo calibration result"""
    visual_counts: Dict[str, int] = Field(..., description="Product counts from image")
    ledger_counts: Dict[str, int] = Field(..., description="Current ledger counts")
    discrepancies: List[Dict] = Field(..., description="Products with count mismatch")
    confidence_scores: Dict[str, float] = Field(..., description="Detection confidence")
    needs_confirmation: bool = Field(..., description="Whether owner confirmation needed")
