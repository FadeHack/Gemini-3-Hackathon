"""
Gemini-related Pydantic models
Defines models for Gemini API responses and reasoning steps
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class ReasoningStep(BaseModel):
    """Single step in AI reasoning chain"""
    step_number: int = Field(..., ge=1, description="Step sequence number")
    step_type: Literal[
        "SHELF_ANALYSIS",
        "PARCHI_READING",
        "VOICE_PROCESSING",
        "DEMAND_FORECAST",
        "PRICE_COMPARISON",
        "ORDER_GENERATION",
        "INVENTORY_UPDATE",
        "UDHAAR_UPDATE"
    ] = Field(..., description="Type of reasoning step")
    icon: str = Field(..., description="Emoji icon for UI")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional step details"
    )
    status: Literal["in_progress", "completed", "failed"] = Field(
        "completed",
        description="Step status"
    )
    timestamp: str = Field(..., description="ISO timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "step_type": "SHELF_ANALYSIS",
                "icon": "🔍",
                "title": "Shelf Analysis",
                "description": "Detected 15 products on shelf",
                "details": {
                    "status": "completed",
                    "products_detected": 15,
                    "critical_low": 4,
                    "processing_time_ms": 1850
                },
                "status": "completed",
                "timestamp": "2026-02-14T14:30:04Z"
            }
        }


class ParchiTransaction(BaseModel):
    """Transaction extracted from kacchi parchi"""
    product: str = Field(..., description="Product name (may be shorthand)")
    quantity: int = Field(..., gt=0, description="Quantity sold")
    price: Optional[float] = Field(None, description="Price (if mentioned)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence")
    product_id: Optional[str] = Field(None, description="Matched product SKU")


class UncertainItem(BaseModel):
    """Item with low OCR confidence"""
    text_recognized: str = Field(..., description="What was recognized")
    confidence: float = Field(..., ge=0.0, le=1.0)
    possible_products: List[str] = Field(
        default_factory=list,
        description="Possible product matches"
    )
    needs_confirmation: bool = Field(True)


class ShelfAnalysisResult(BaseModel):
    """Shelf photo analysis result"""
    products_detected: int = Field(..., ge=0)
    products: List[Dict[str, Any]] = Field(..., description="Detected products with counts")
    critical_low: int = Field(0, ge=0, description="Count of critically low items")
    empty_shelf_spaces: int = Field(0, ge=0, description="Empty shelf spots detected")
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    processing_time_ms: int = Field(..., gt=0)


class GeminiResponse(BaseModel):
    """Complete Gemini API response"""
    response_type: Literal[
        "shelf_analysis",
        "procurement",
        "forecast",
        "general",
        "inventory_update",
        "parchi_reading",
        "voice_processing"
    ] = Field(..., description="Type of response")

    raw_response: str = Field(..., description="Raw text response from Gemini")

    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parsed structured data from response"
    )

    reasoning_steps: List[ReasoningStep] = Field(
        default_factory=list,
        description="Step-by-step reasoning chain"
    )

    message_to_owner: str = Field(
        ...,
        description="Message for store owner in Hinglish"
    )

    # Optional fields based on response type
    procurement_order: Optional[Dict[str, Any]] = Field(
        None,
        description="Procurement order if generated"
    )

    inventory_alerts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Inventory alerts"
    )

    transactions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Transactions from parchi/voice"
    )

    uncertain_items: Optional[List[UncertainItem]] = Field(
        None,
        description="Items with low confidence"
    )

    daily_summary_update: Optional[Dict[str, Any]] = Field(
        None,
        description="Daily P&L summary updates"
    )

    shelf_analysis: Optional[ShelfAnalysisResult] = Field(
        None,
        description="Shelf analysis details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response_type": "shelf_analysis",
                "reasoning_steps": [],
                "message_to_owner": "Rajesh bhai, aapki shelf dekhi maine. Maggi aur Surf Excel critically low hai...",
                "inventory_alerts": [],
                "procurement_order": {}
            }
        }


class GeminiRequest(BaseModel):
    """Request to Gemini API"""
    prompt: str = Field(..., description="User prompt or system instruction")
    image_data: Optional[str] = Field(None, description="Base64 encoded image")
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (store profile, festival, weather)"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
