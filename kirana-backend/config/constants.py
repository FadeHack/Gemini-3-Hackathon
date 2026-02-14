"""
Application constants, enums, and multipliers
Defines festival multipliers, weather factors, and business rules
"""

from enum import Enum
from typing import Dict


# ============================================================================
# ENUMS
# ============================================================================

class MessageType(str, Enum):
    """Message types supported"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"


class TransactionType(str, Enum):
    """Transaction payment types"""
    CASH = "cash"
    UPI = "upi"
    CREDIT = "credit"
    SUPPLIER_DELIVERY = "supplier_delivery"


class StockStatus(str, Enum):
    """Inventory stock status levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    HEALTHY = "healthy"


class Urgency(str, Enum):
    """Action urgency levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReasoningStepType(str, Enum):
    """Types of AI reasoning steps"""
    SHELF_ANALYSIS = "SHELF_ANALYSIS"
    PARCHI_READING = "PARCHI_READING"
    VOICE_PROCESSING = "VOICE_PROCESSING"
    DEMAND_FORECAST = "DEMAND_FORECAST"
    PRICE_COMPARISON = "PRICE_COMPARISON"
    ORDER_GENERATION = "ORDER_GENERATION"
    INVENTORY_UPDATE = "INVENTORY_UPDATE"
    UDHAAR_UPDATE = "UDHAAR_UPDATE"


class WebSocketEventType(str, Enum):
    """WebSocket event types"""
    CONNECTION_ESTABLISHED = "connection_established"
    REASONING_STEP = "reasoning_step"
    CHAT_MESSAGE = "chat_message"
    INVENTORY_UPDATE = "inventory_update"
    PROCUREMENT_ORDER = "procurement_order"
    UDHAAR_UPDATE = "udhaar_update"
    PNL_UPDATE = "pnl_update"
    ERROR = "error"


# ============================================================================
# FESTIVAL MULTIPLIERS
# ============================================================================

FESTIVAL_MULTIPLIERS = {
    "diwali": {
        "sweets": 4.0,
        "dry_fruits": 3.5,
        "pooja_items": 5.0,
        "decorations": 8.0,
        "snacks": 2.5,
        "fruits": 2.0,
        "dairy": 1.8,
        "cooking_oil": 2.0,
    },
    "navratri": {
        "fasting_food": 3.5,
        "fruits": 2.5,
        "dairy": 2.0,
        "dry_fruits": 2.0,
        "pooja_items": 3.0,
        "sweets": 2.5,
    },
    "holi": {
        "colors": 10.0,
        "sweets": 3.0,
        "snacks": 2.5,
        "beverages": 2.0,
        "fruits": 1.5,
    },
    "raksha_bandhan": {
        "sweets": 3.5,
        "dry_fruits": 2.5,
        "snacks": 2.0,
        "gifts": 4.0,
    },
    "eid": {
        "dates": 5.0,
        "sewaiyan": 4.0,
        "dry_fruits": 3.0,
        "sweets": 3.5,
        "dairy": 2.5,
        "fruits": 2.0,
    },
    "janmashtami": {
        "dairy": 3.0,
        "sweets": 2.5,
        "fasting_food": 2.0,
        "fruits": 2.0,
        "pooja_items": 2.5,
    },
    "ganesh_chaturthi": {
        "pooja_items": 4.0,
        "sweets": 3.5,
        "fruits": 2.5,
        "flowers": 5.0,
        "decorations": 3.0,
    },
    "makar_sankranti": {
        "til_gud": 5.0,
        "jaggery": 3.0,
        "peanuts": 3.0,
        "kites": 8.0,
        "sweets": 2.0,
    },
    "durga_puja": {
        "sweets": 4.5,
        "fish": 3.0,
        "fruits": 2.5,
        "pooja_items": 4.0,
        "flowers": 5.0,
        "decorations": 4.0,
    },
    "pongal": {
        "rice": 3.5,
        "jaggery": 3.0,
        "sugarcane": 4.0,
        "turmeric": 2.5,
        "dairy": 2.0,
    },
}


# ============================================================================
# WEATHER MULTIPLIERS
# ============================================================================

def get_weather_multiplier(category: str, temp_c: float, condition: str) -> float:
    """
    Calculate weather-based demand multiplier

    Args:
        category: Product category
        temp_c: Temperature in Celsius
        condition: Weather condition (clear, rain, cloudy, etc.)

    Returns:
        Multiplier (1.0 = no change)
    """
    multiplier = 1.0

    # Temperature-based
    if category == "beverages":
        if temp_c > 35:
            multiplier = 1.4  # Hot weather → more cold drinks
        elif temp_c > 30:
            multiplier = 1.2
        elif temp_c < 15:
            multiplier = 0.8  # Cold weather → less cold drinks

    elif category in ["instant_food", "snacks"]:
        if temp_c < 20:
            multiplier = 1.2  # Cold weather → more snacks
        elif condition == "rain":
            multiplier = 1.3  # Rainy → people buy instant food

    elif category == "ice_cream":
        if temp_c > 35:
            multiplier = 2.0
        elif temp_c > 30:
            multiplier = 1.5
        elif temp_c < 20:
            multiplier = 0.5

    # Condition-based
    if condition == "rain":
        if category in ["umbrella", "raincoat"]:
            multiplier = 3.0
        elif category in ["instant_food", "snacks", "bakery"]:
            multiplier = max(multiplier, 1.3)

    return multiplier


# ============================================================================
# DAY OF WEEK MULTIPLIERS
# ============================================================================

DAY_OF_WEEK_MULTIPLIERS = {
    "Monday": {
        "default": 0.9,  # Generally slower after weekend
    },
    "Tuesday": {
        "default": 0.95,
    },
    "Wednesday": {
        "default": 1.0,
    },
    "Thursday": {
        "default": 1.0,
    },
    "Friday": {
        "default": 1.1,  # Weekend prep starts
        "snacks": 1.2,
        "beverages": 1.2,
    },
    "Saturday": {
        "default": 1.2,  # Weekend shopping
        "snacks": 1.3,
        "beverages": 1.3,
    },
    "Sunday": {
        "default": 1.3,  # Highest shopping day
        "snacks": 1.4,
        "bakery": 1.5,  # Breakfast items
        "dairy": 1.3,
    },
}


def get_dow_multiplier(category: str, day_of_week: str) -> float:
    """
    Get day-of-week demand multiplier

    Args:
        category: Product category
        day_of_week: Day name (Monday, Tuesday, etc.)

    Returns:
        Multiplier (1.0 = no change)
    """
    dow_data = DAY_OF_WEEK_MULTIPLIERS.get(day_of_week, {"default": 1.0})
    return dow_data.get(category, dow_data.get("default", 1.0))


# ============================================================================
# STOCK THRESHOLDS
# ============================================================================

STOCK_THRESHOLDS = {
    "critical_days": 1.0,  # Less than 1 day of stock
    "warning_days": 3.0,   # Less than 3 days of stock
    "healthy_days": 3.0,   # 3+ days of stock
}


# ============================================================================
# REASONING STEP ICONS
# ============================================================================

REASONING_STEP_ICONS = {
    ReasoningStepType.SHELF_ANALYSIS: "🔍",
    ReasoningStepType.PARCHI_READING: "📝",
    ReasoningStepType.VOICE_PROCESSING: "🎤",
    ReasoningStepType.DEMAND_FORECAST: "📊",
    ReasoningStepType.PRICE_COMPARISON: "💰",
    ReasoningStepType.ORDER_GENERATION: "🛒",
    ReasoningStepType.INVENTORY_UPDATE: "📦",
    ReasoningStepType.UDHAAR_UPDATE: "💳",
}


# ============================================================================
# UPI CONFIGURATION
# ============================================================================

UPI_CONFIG = {
    "base_url": "upi://pay",
    "timeout_hours": 24,  # Payment link validity
}


# ============================================================================
# DEMO MODE RESPONSES
# ============================================================================

DEMO_RESPONSE_PATHS = {
    "shelf": "./demo/shelf_response.json",
    "parchi": "./demo/parchi_response.json",
    "voice": "./demo/voice_response.json",
}
