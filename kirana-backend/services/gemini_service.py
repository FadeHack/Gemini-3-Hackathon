"""
Gemini AI service for multimodal processing
Handles text, image, and voice processing with the Gemini API
"""

import json
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

import google.generativeai as genai
from config.settings import settings
from config.system_prompt import get_prompt
from models.gemini import GeminiResponse, ReasoningStep


class GeminiService:
    """Service for interacting with Gemini API"""

    def __init__(self):
        """Initialize Gemini service"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.demo_mode = settings.DEMO_MODE

        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(
            f"GeminiService initialized with model={self.model_name}, "
            f"demo_mode={self.demo_mode}"
        )

    async def process_shelf_photo(
        self,
        image_data: str,
        store_context: Dict[str, Any],
        product_catalog: List[Dict[str, Any]]
    ) -> GeminiResponse:
        """
        Process shelf photo to detect products and generate recommendations

        Args:
            image_data: Base64 encoded image
            store_context: Store profile and contextual information
            product_catalog: List of available products

        Returns:
            GeminiResponse with product detection and recommendations
        """
        if self.demo_mode:
            return await self._load_demo_response("shelf")

        try:
            # Get system prompt
            prompt = get_prompt("shelf_photo", store_context)

            # Add product catalog context
            catalog_text = "\n\nPRODUCT CATALOG:\n"
            for product in product_catalog:
                catalog_text += (
                    f"- {product['name']} ({product['sku_id']}): "
                    f"MRP ₹{product['mrp']}, Category: {product['category']}\n"
                )

            full_prompt = prompt + catalog_text

            # Decode base64 image
            image_bytes = base64.b64decode(image_data)

            # Create multimodal input
            logger.info("Sending shelf photo to Gemini API...")
            response = self.model.generate_content([
                full_prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])

            # Parse response
            result = self._parse_gemini_response(response, "shelf_analysis")
            logger.success("Shelf photo processed successfully")

            return result

        except Exception as e:
            logger.error(f"Error processing shelf photo: {e}")
            raise

    async def process_parchi_image(
        self,
        image_data: str,
        store_context: Dict[str, Any],
        product_catalog: List[Dict[str, Any]]
    ) -> GeminiResponse:
        """
        Process kacchi parchi (handwritten sales slip) OCR

        Args:
            image_data: Base64 encoded image of parchi
            store_context: Store profile and contextual information
            product_catalog: List of available products

        Returns:
            GeminiResponse with extracted transactions
        """
        if self.demo_mode:
            return await self._load_demo_response("parchi")

        try:
            # Get system prompt
            prompt = get_prompt("parchi_reading", store_context)

            # Add product catalog for matching
            catalog_text = "\n\nPRODUCT CATALOG (for matching):\n"
            for product in product_catalog:
                catalog_text += (
                    f"- {product['name']} / {product['name_hi']} "
                    f"({product['sku_id']})\n"
                )

            full_prompt = prompt + catalog_text

            # Decode base64 image
            image_bytes = base64.b64decode(image_data)

            # Create multimodal input
            logger.info("Sending parchi to Gemini API for OCR...")
            response = self.model.generate_content([
                full_prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])

            # Parse response
            result = self._parse_gemini_response(response, "parchi_reading")
            logger.success("Parchi processed successfully")

            return result

        except Exception as e:
            logger.error(f"Error processing parchi: {e}")
            raise

    async def process_voice_message(
        self,
        audio_data: str,
        store_context: Dict[str, Any]
    ) -> GeminiResponse:
        """
        Process voice message (transcribe + understand intent)

        Args:
            audio_data: Base64 encoded audio (wav/mp3/ogg)
            store_context: Store profile and contextual information

        Returns:
            GeminiResponse with transcription and extracted intent
        """
        if self.demo_mode:
            return await self._load_demo_response("voice")

        try:
            # Get system prompt
            prompt = get_prompt("voice_message", store_context)

            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)

            # Create multimodal input
            logger.info("Sending voice message to Gemini API...")
            response = self.model.generate_content([
                prompt,
                {"mime_type": "audio/wav", "data": audio_bytes}
            ])

            # Parse response
            result = self._parse_gemini_response(response, "voice_processing")
            logger.success("Voice message processed successfully")

            return result

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            raise

    async def process_text_query(
        self,
        query: str,
        store_context: Dict[str, Any]
    ) -> GeminiResponse:
        """
        Process general text query with automatic momentum detection

        Args:
            query: User's text query
            store_context: Store profile and contextual information (may include sales_history)

        Returns:
            GeminiResponse with answer
        """
        try:
            # Get system prompt
            prompt = get_prompt("general_query", store_context)

            # Add sales history for momentum detection if available
            sales_history_text = ""
            if "sales_history" in store_context:
                sales_history = store_context["sales_history"]
                sales_history_text = "\n\n**SALES HISTORY (for momentum detection):**\n"

                for product_id, product_data in sales_history.get("products", {}).items():
                    sales_history_text += f"\n{product_id}:\n"
                    sales_history_text += f"- Typical daily: {product_data['typical_daily_sales']}\n"
                    sales_history_text += f"- 30-day average: {product_data['stats']['average_daily']}\n"
                    sales_history_text += f"- Weekend avg: {product_data['stats']['weekend_average']}\n"
                    sales_history_text += f"- Rainy day avg: {product_data['stats']['rainy_day_average']}\n"

            # Combine with user query
            full_prompt = f"{prompt}{sales_history_text}\n\nUSER QUERY: {query}"

            # Send to Gemini
            logger.info(f"Processing text query: {query[:50]}...")
            response = self.model.generate_content(full_prompt)

            # Parse response
            result = self._parse_gemini_response(response, "general")
            logger.success("Text query processed successfully")

            return result

        except Exception as e:
            logger.error(f"Error processing text query: {e}")
            raise

    async def generate_demand_forecast_explanation(
        self,
        forecast_data: Dict[str, Any],
        store_context: Dict[str, Any]
    ) -> str:
        """
        Generate natural language explanation of demand forecast

        Args:
            forecast_data: Forecast results from demand_forecast engine
            store_context: Store profile and contextual information

        Returns:
            Natural language explanation in Hinglish
        """
        try:
            # Get system prompt
            prompt = get_prompt("demand_forecast", store_context)

            # Add forecast data
            forecast_text = f"\n\nFORECAST DATA:\n{json.dumps(forecast_data, indent=2)}"
            full_prompt = prompt + forecast_text

            # Send to Gemini
            logger.info("Generating forecast explanation...")
            response = self.model.generate_content(full_prompt)

            explanation = response.text.strip()
            logger.success("Forecast explanation generated")

            return explanation

        except Exception as e:
            logger.error(f"Error generating forecast explanation: {e}")
            return "Forecast generated successfully. Check details above."

    async def process_momentum_detection(
        self,
        user_message: str,
        store_context: Dict[str, Any],
        sales_history: Dict[str, Any],
        current_inventory: Dict[str, Any],
        product_catalog: List[Dict[str, Any]],
        weather_forecast: Optional[List[Dict[str, Any]]] = None
    ) -> GeminiResponse:
        """
        Detect sales momentum and recommend smart surplus ordering

        Args:
            user_message: Owner's message about fast sales
            store_context: Store profile and contextual information
            sales_history: 30-day sales history data
            current_inventory: Current stock levels
            product_catalog: List of available products
            weather_forecast: Weather forecast for next 48 hours

        Returns:
            GeminiResponse with momentum analysis and procurement recommendation
        """
        try:
            # Add time context
            from datetime import datetime
            now = datetime.now()
            store_context["current_day"] = now.strftime("%A")
            store_context["current_time"] = now.strftime("%I:%M %p")
            store_context["weather_forecast"] = weather_forecast or []

            # Get system prompt
            prompt = get_prompt("momentum_detection", store_context)

            # Add sales history context
            history_text = "\n\n30-DAY SALES HISTORY:\n"
            for product_id, product_data in sales_history.get("products", {}).items():
                history_text += f"\n**{product_id}**\n"
                history_text += f"- Typical daily sales: {product_data['typical_daily_sales']}\n"
                history_text += f"- Average daily: {product_data['stats']['average_daily']}\n"
                history_text += f"- Weekend average: {product_data['stats']['weekend_average']}\n"
                history_text += f"- Weekday average: {product_data['stats']['weekday_average']}\n"
                history_text += f"- Rainy day average: {product_data['stats']['rainy_day_average']}\n"

                # Include recent 7 days
                recent_sales = product_data['daily_sales'][-7:]
                history_text += "- Recent 7 days: "
                history_text += ", ".join([
                    f"{s['date'][-5:]}: {s['quantity']}"
                    for s in recent_sales
                ])
                history_text += "\n"

            # Add current inventory context
            inventory_text = "\n\nCURRENT INVENTORY:\n"
            for product_id, inv_data in current_inventory.items():
                inventory_text += (
                    f"- {product_id}: {inv_data.get('current_stock', 0)} units "
                    f"(sold today: {inv_data.get('today_sold', 0)})\n"
                )

            # Add product catalog with prices
            catalog_text = "\n\nPRODUCT CATALOG (for pricing):\n"
            for product in product_catalog:
                catalog_text += (
                    f"- {product['name']} ({product['sku_id']}): "
                    f"Purchase ₹{product['avg_purchase_price']}, "
                    f"MRP ₹{product['mrp']}\n"
                )

            # Add weather forecast
            forecast_text = ""
            if weather_forecast:
                forecast_text = "\n\nWEATHER FORECAST (Next 48h):\n"
                for f in weather_forecast[:2]:
                    forecast_text += (
                        f"- {f.get('date')}: {f.get('condition', 'clear').title()}, "
                        f"{f.get('temp_min')}°C - {f.get('temp_max')}°C"
                    )
                    if f.get('rain_probability'):
                        forecast_text += " (Rain likely)"
                    forecast_text += "\n"

            # Combine all context
            full_prompt = (
                prompt +
                history_text +
                inventory_text +
                catalog_text +
                forecast_text +
                f"\n\n**OWNER'S MESSAGE:**\n{user_message}"
            )

            # Send to Gemini
            logger.info(f"Processing momentum detection: {user_message[:50]}...")
            response = self.model.generate_content(full_prompt)

            # Parse response
            result = self._parse_gemini_response(response, "momentum_detection")
            logger.success("Momentum detection processed successfully")

            return result

        except Exception as e:
            logger.error(f"Error processing momentum detection: {e}")
            raise

    def _parse_gemini_response(
        self,
        response: Any,
        response_type: str
    ) -> GeminiResponse:
        """
        Parse Gemini API response into structured format

        Args:
            response: Raw Gemini API response
            response_type: Type of response (shelf_photo, parchi_reading, etc.)

        Returns:
            Structured GeminiResponse
        """
        try:
            # Extract text response
            text_response = response.text.strip()

            # Try to parse as JSON (structured responses)
            try:
                # Remove markdown code blocks if present
                if text_response.startswith("```json"):
                    text_response = text_response.replace("```json", "").replace("```", "").strip()
                elif text_response.startswith("```"):
                    text_response = text_response.replace("```", "").strip()

                parsed_data = json.loads(text_response)

                # Extract reasoning steps if present
                reasoning_steps = []
                if "reasoning_steps" in parsed_data:
                    for step in parsed_data["reasoning_steps"]:
                        # Handle both dict and string formats
                        if isinstance(step, dict):
                            reasoning_steps.append(ReasoningStep(
                                step_type=step.get("type", step.get("step_type", "ANALYSIS")),
                                description=step.get("description", ""),
                                details=step.get("details", {})
                            ))
                        else:
                            # Skip non-dict entries
                            logger.warning(f"Skipping non-dict reasoning step: {type(step)}")

                # Extract message to owner
                message = parsed_data.get(
                    "message_to_owner",
                    parsed_data.get("message", "")
                )

                return GeminiResponse(
                    response_type=response_type,
                    raw_response=text_response,
                    structured_data=parsed_data,
                    reasoning_steps=reasoning_steps,
                    message_to_owner=message
                )

            except json.JSONDecodeError:
                # If not JSON, treat as plain text response
                logger.warning("Response is not valid JSON, treating as plain text")
                return GeminiResponse(
                    response_type=response_type,
                    raw_response=text_response,
                    structured_data={},
                    reasoning_steps=[],
                    message_to_owner=text_response
                )

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            raise

    async def _load_demo_response(self, response_type: str) -> GeminiResponse:
        """
        Load cached demo response (for demo mode without API calls)

        Args:
            response_type: Type of response (shelf, parchi, voice)

        Returns:
            Cached GeminiResponse
        """
        from config.constants import DEMO_RESPONSE_PATHS

        try:
            demo_path = DEMO_RESPONSE_PATHS.get(response_type)
            if not demo_path:
                raise ValueError(f"No demo response for type: {response_type}")

            path = Path(demo_path)
            if not path.exists():
                logger.warning(f"Demo response file not found: {demo_path}")
                # Return placeholder
                return GeminiResponse(
                    response_type=f"{response_type}_demo",
                    raw_response="{}",
                    structured_data={},
                    reasoning_steps=[],
                    message_to_owner="Demo response (file not found)"
                )

            # Load cached response
            with open(path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            logger.info(f"Loaded demo response from {demo_path}")

            # Parse cached data into GeminiResponse
            reasoning_steps = []
            if "reasoning_steps" in cached_data:
                for step in cached_data["reasoning_steps"]:
                    reasoning_steps.append(ReasoningStep(
                        step_type=step.get("type", "ANALYSIS"),
                        description=step.get("description", ""),
                        details=step.get("details", {})
                    ))

            return GeminiResponse(
                response_type=f"{response_type}_demo",
                raw_response=json.dumps(cached_data),
                structured_data=cached_data,
                reasoning_steps=reasoning_steps,
                message_to_owner=cached_data.get(
                    "message_to_owner",
                    cached_data.get("message", "")
                )
            )

        except Exception as e:
            logger.error(f"Error loading demo response: {e}")
            raise


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create GeminiService singleton"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service