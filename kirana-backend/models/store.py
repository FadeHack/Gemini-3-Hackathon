"""
Store-related Pydantic models
Defines StoreProfile, Product, Distributor, and inventory state
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class Product(BaseModel):
    """Individual product definition"""
    sku_id: str = Field(..., description="Unique SKU identifier")
    name: str = Field(..., description="Product name in English")
    name_hi: str = Field(..., description="Product name in Hindi")
    name_local: Optional[str] = Field(None, description="Regional language name")
    category: str = Field(..., description="Product category")
    mrp: float = Field(..., description="Maximum Retail Price")
    avg_purchase_price: float = Field(..., description="Average purchase price")
    unit: str = Field(..., description="Unit type (packet, kg, liter, etc.)")
    reorder_point: int = Field(..., description="Minimum stock level before reorder")
    typical_daily_sales: float = Field(..., description="Average daily sales velocity")
    festival_boost: Optional[Dict[str, float]] = Field(
        None,
        description="Festival-specific demand multipliers"
    )


class InventoryItem(BaseModel):
    """Current inventory state for a product"""
    sku_id: str
    product_name: str
    current_stock: int = Field(..., ge=0, description="Current stock level")
    today_sold: int = Field(0, ge=0, description="Items sold today")
    today_received: int = Field(0, ge=0, description="Items received today")
    today_revenue: float = Field(0.0, ge=0.0, description="Revenue from this item today")
    avg_daily_sales: float = Field(..., description="Average daily velocity")
    days_of_stock: float = Field(..., description="Days until stockout at current velocity")
    status: str = Field(..., description="Stock status: critical/warning/healthy")
    reorder_point: int = Field(...)
    mrp: float = Field(...)
    purchase_price: float = Field(...)


class Distributor(BaseModel):
    """Distributor/supplier profile"""
    id: str = Field(..., description="Unique distributor ID")
    name: str = Field(..., description="Distributor business name")
    contact_person: str = Field(..., description="Contact person name")
    phone: str = Field(..., description="Contact phone number")
    upi_id: str = Field(..., description="UPI ID for payments")
    address: str = Field(..., description="Business address")
    delivery_days: int = Field(..., ge=0, description="Delivery time in days")
    minimum_order: float = Field(..., ge=0, description="Minimum order value")
    price_tier: str = Field(..., description="Pricing category")
    categories: List[str] = Field(..., description="Categories supplied")
    payment_terms: str = Field(..., description="Payment terms")
    reliability_score: float = Field(..., ge=0.0, le=5.0, description="Reliability rating")
    products: Dict[str, float] = Field(..., description="Product SKU to price mapping")


class UdhaarCustomer(BaseModel):
    """Credit ledger for a customer"""
    name: str = Field(..., description="Customer name")
    total_outstanding: float = Field(..., ge=0.0, description="Total outstanding amount")
    transactions_count: int = Field(..., ge=0, description="Number of credit transactions")
    last_transaction_date: str = Field(..., description="Last transaction date")
    transactions: List[Dict] = Field(default_factory=list, description="Transaction history")


class DailySummary(BaseModel):
    """Daily P&L summary"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    total_revenue: float = Field(0.0, ge=0.0)
    total_transactions: int = Field(0, ge=0)
    cash_collected: float = Field(0.0, ge=0.0)
    upi_collected: float = Field(0.0, ge=0.0)
    credit_given: float = Field(0.0, ge=0.0)
    items_sold: int = Field(0, ge=0)
    items_received: int = Field(0, ge=0)
    unique_customers: int = Field(0, ge=0)


class StorePreferences(BaseModel):
    """Store owner preferences"""
    preferred_distributors: List[str] = Field(default_factory=list)
    reorder_threshold_days: int = Field(3, ge=1, le=30)
    auto_order_enabled: bool = Field(False)
    notification_time: str = Field("09:00")
    language_preference: str = Field("hinglish")


class StoreMetadata(BaseModel):
    """Store metadata and stats"""
    created_at: str = Field(...)
    last_updated: str = Field(...)
    total_products: int = Field(..., ge=0)
    critical_stock_count: int = Field(0, ge=0)
    warning_stock_count: int = Field(0, ge=0)
    healthy_stock_count: int = Field(0, ge=0)


class StoreProfile(BaseModel):
    """Complete store profile with all state"""
    store_id: str = Field(..., description="Unique store identifier")
    name: str = Field(..., description="Store name")
    owner_name: str = Field(..., description="Owner name")
    phone: str = Field(..., description="Contact phone")
    language: str = Field("hinglish", description="Preferred language")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., description="Postal code")
    address: str = Field(..., description="Store address")
    store_type: str = Field("neighborhood_kirana")
    established_year: int = Field(..., ge=1900, le=2100)
    avg_monthly_revenue: float = Field(..., ge=0.0)

    current_inventory: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Current inventory state by SKU"
    )
    udhaar_ledger: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Credit ledger by customer name"
    )
    daily_summary: DailySummary = Field(...)
    preferences: StorePreferences = Field(default_factory=StorePreferences)
    metadata: StoreMetadata = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "store_id": "sharma_general_store",
                "name": "Sharma General Store",
                "owner_name": "Rajesh Sharma",
                "phone": "+91-98765-12345",
                "city": "Indore",
                "state": "Madhya Pradesh",
            }
        }


class InventorySummary(BaseModel):
    """Quick inventory summary"""
    total_items: int = Field(..., ge=0)
    critical_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)
    healthy_count: int = Field(0, ge=0)
    total_value: float = Field(0.0, ge=0.0)
    last_updated: str = Field(...)
