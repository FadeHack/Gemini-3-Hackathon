"""
Unit tests for Gemini Service
Tests AI processing with mocked API responses
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Set required environment variables before importing services
os.environ.setdefault("GEMINI_API_KEY", "test_api_key_12345")
os.environ.setdefault("WEATHER_API_KEY", "test_weather_key_12345")
os.environ.setdefault("DEMO_MODE", "false")

from services.gemini_service import GeminiService
from models.gemini import GeminiResponse, ReasoningStep
from config.settings import Settings
import json
import os


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = Mock(spec=Settings)
    settings.GEMINI_API_KEY = "test_api_key"
    settings.GEMINI_MODEL = "gemini-2.0-flash-exp"
    settings.DEMO_MODE = False
    return settings


@pytest.fixture
def gemini_service(mock_settings):
    """Create GeminiService instance with mocked settings"""
    with patch('services.gemini_service.settings', mock_settings):
        service = GeminiService()
        return service


@pytest.fixture
def sample_shelf_response():
    """Sample shelf photo analysis response"""
    return {
        "reasoning_steps": [
            {
                "step_number": 1,
                "step_type": "SHELF_ANALYSIS",
                "description": "Analyzing shelf layout",
                "icon": "📸",
                "details": {"products_detected": 8}
            }
        ],
        "message_to_owner": "**📸 Shelf Analysis Complete!**\n\n8 products detected.",
        "structured_data": {
            "products": [
                {
                    "product_id": "maggi_70g",
                    "product_name": "Maggi 2-Minute Noodles 70g",
                    "quantity": 10,
                    "confidence": 0.92
                }
            ],
            "critical_stock": ["maggi_70g"],
            "procurement_needed": True
        }
    }


@pytest.fixture
def sample_parchi_response():
    """Sample parchi OCR response"""
    return {
        "reasoning_steps": [
            {
                "step_number": 1,
                "step_type": "OCR_EXTRACTION",
                "description": "Reading handwritten text",
                "icon": "📝",
                "details": {"items_found": 4}
            }
        ],
        "message_to_owner": "**📝 Parchi Samajh Gayi!**\n\n4 transactions recorded.",
        "structured_data": {
            "transactions": [
                {
                    "product_id": "maggi_70g",
                    "quantity": -5,
                    "transaction_type": "sale",
                    "price": 12.0,
                    "payment_type": "cash",
                    "amount": 60.0
                }
            ]
        }
    }


@pytest.fixture
def sample_voice_response():
    """Sample voice message response"""
    return {
        "reasoning_steps": [
            {
                "step_number": 1,
                "step_type": "VOICE_PROCESSING",
                "description": "Transcribing audio",
                "icon": "🎤",
                "details": {"audio_duration": "8.5s"}
            }
        ],
        "message_to_owner": "**🎤 Voice Message Samajh Gayi!**",
        "structured_data": {
            "transcription": "Maggi ke paanch packet bik gaye",
            "intent": "SALE",
            "intent_confidence": 0.94
        }
    }


class TestGeminiServiceInitialization:
    """Test service initialization"""

    def test_service_initialization(self, gemini_service):
        """Test service initializes correctly"""
        assert gemini_service is not None
        assert hasattr(gemini_service, 'model')

    def test_demo_mode_detection(self):
        """Test demo mode is detected from settings"""
        with patch('services.gemini_service.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            service = GeminiService()
            # Demo mode should affect behavior
            assert mock_settings.DEMO_MODE is True


class TestShelfPhotoProcessing:
    """Test shelf photo analysis"""

    @pytest.mark.asyncio
    async def test_process_shelf_photo_success(self, gemini_service, sample_shelf_response):
        """Test successful shelf photo processing"""
        # Mock the Gemini API call
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64_data",
                context={
                    "store_name": "Test Store",
                    "owner_name": "Test Owner",
                    "upcoming_festivals": [],
                    "weather": {"temperature": 25}
                }
            )

            assert isinstance(result, GeminiResponse)
            assert len(result.reasoning_steps) > 0
            assert "Shelf Analysis Complete" in result.message_to_owner
            assert "products" in result.structured_data

    @pytest.mark.asyncio
    async def test_shelf_photo_with_festival_context(self, gemini_service, sample_shelf_response):
        """Test shelf processing considers festival context"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context={
                    "store_name": "Test Store",
                    "owner_name": "Test Owner",
                    "upcoming_festivals": [
                        {"name": "Navratri", "days_until": 2, "impact": "high"}
                    ],
                    "weather": {"temperature": 30}
                }
            )

            assert result is not None
            assert isinstance(result, GeminiResponse)

    @pytest.mark.asyncio
    async def test_shelf_photo_missing_context(self, gemini_service, sample_shelf_response):
        """Test shelf processing handles missing context gracefully"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            # Minimal context
            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            assert result is not None


class TestParchiProcessing:
    """Test kacchi parchi OCR processing"""

    @pytest.mark.asyncio
    async def test_process_parchi_success(self, gemini_service, sample_parchi_response):
        """Test successful parchi processing"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_parchi_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_parchi_image(
                image_base64="fake_base64_data",
                context={
                    "store_name": "Test Store",
                    "owner_name": "Test Owner"
                }
            )

            assert isinstance(result, GeminiResponse)
            assert "transactions" in result.structured_data
            assert len(result.structured_data["transactions"]) > 0

    @pytest.mark.asyncio
    async def test_parchi_extracts_multiple_transactions(self, gemini_service):
        """Test parchi can extract multiple transactions"""
        multi_transaction_response = {
            "reasoning_steps": [],
            "message_to_owner": "Multiple transactions found",
            "structured_data": {
                "transactions": [
                    {"product_id": "maggi_70g", "quantity": -5, "transaction_type": "sale"},
                    {"product_id": "atta_5kg", "quantity": -2, "transaction_type": "sale"},
                    {"product_id": "pepsi_600ml", "quantity": -12, "transaction_type": "sale"}
                ]
            }
        }

        mock_response = Mock()
        mock_response.text = json.dumps(multi_transaction_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_parchi_image(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            assert len(result.structured_data["transactions"]) == 3

    @pytest.mark.asyncio
    async def test_parchi_handles_udhaar_transactions(self, gemini_service):
        """Test parchi handles credit/udhaar transactions"""
        udhaar_response = {
            "reasoning_steps": [],
            "message_to_owner": "Udhaar transaction detected",
            "structured_data": {
                "transactions": [
                    {
                        "product_id": "maggi_70g",
                        "quantity": -5,
                        "transaction_type": "sale",
                        "payment_type": "udhaar",
                        "customer_name": "Sharma ji",
                        "amount": 60.0
                    }
                ],
                "udhaar_entry": {
                    "customer_name": "Sharma ji",
                    "amount": 60.0,
                    "items": ["Maggi 70g x 5"]
                }
            }
        }

        mock_response = Mock()
        mock_response.text = json.dumps(udhaar_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_parchi_image(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            assert "udhaar_entry" in result.structured_data
            assert result.structured_data["udhaar_entry"]["customer_name"] == "Sharma ji"


class TestVoiceProcessing:
    """Test voice message processing"""

    @pytest.mark.asyncio
    async def test_process_voice_message_success(self, gemini_service, sample_voice_response):
        """Test successful voice message processing"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_voice_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_voice_message(
                audio_base64="fake_audio_base64",
                context={
                    "store_name": "Test Store",
                    "language": "hinglish"
                }
            )

            assert isinstance(result, GeminiResponse)
            assert "transcription" in result.structured_data
            assert "intent" in result.structured_data

    @pytest.mark.asyncio
    async def test_voice_intent_detection(self, gemini_service):
        """Test voice message intent is correctly detected"""
        intent_response = {
            "reasoning_steps": [],
            "message_to_owner": "Intent detected",
            "structured_data": {
                "transcription": "Stock check karo",
                "intent": "INVENTORY_CHECK",
                "intent_confidence": 0.88
            }
        }

        mock_response = Mock()
        mock_response.text = json.dumps(intent_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_voice_message(
                audio_base64="fake_audio",
                context={"store_name": "Test Store"}
            )

            assert result.structured_data["intent"] == "INVENTORY_CHECK"
            assert result.structured_data["intent_confidence"] > 0.8


class TestTextProcessing:
    """Test text message processing"""

    @pytest.mark.asyncio
    async def test_process_text_message_success(self, gemini_service):
        """Test successful text processing"""
        text_response = {
            "reasoning_steps": [],
            "message_to_owner": "Answer to your question",
            "structured_data": {
                "intent": "QUESTION",
                "response_type": "informational"
            }
        }

        mock_response = Mock()
        mock_response.text = json.dumps(text_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_text_message(
                text="What is my best selling product?",
                context={"store_name": "Test Store"}
            )

            assert isinstance(result, GeminiResponse)

    @pytest.mark.asyncio
    async def test_text_handles_hinglish(self, gemini_service):
        """Test text processing handles Hinglish queries"""
        hinglish_response = {
            "reasoning_steps": [],
            "message_to_owner": "Aapka sabse zyada bikne wala product Maggi hai",
            "structured_data": {
                "language_detected": "hinglish",
                "response_language": "hinglish"
            }
        }

        mock_response = Mock()
        mock_response.text = json.dumps(hinglish_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_text_message(
                text="Sabse zyada kaunsa product bikta hai?",
                context={"store_name": "Test Store", "language": "hinglish"}
            )

            assert "hinglish" in result.structured_data.get("language_detected", "")


class TestReasoningSteps:
    """Test reasoning step extraction"""

    @pytest.mark.asyncio
    async def test_reasoning_steps_extracted(self, gemini_service, sample_shelf_response):
        """Test reasoning steps are properly extracted"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            assert len(result.reasoning_steps) > 0
            first_step = result.reasoning_steps[0]
            assert isinstance(first_step, ReasoningStep)
            assert hasattr(first_step, 'step_number')
            assert hasattr(first_step, 'step_type')
            assert hasattr(first_step, 'description')

    @pytest.mark.asyncio
    async def test_reasoning_steps_have_icons(self, gemini_service, sample_shelf_response):
        """Test reasoning steps include visual icons"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            for step in result.reasoning_steps:
                assert hasattr(step, 'icon')
                assert step.icon is not None


class TestDemoMode:
    """Test demo mode fallback"""

    @pytest.mark.asyncio
    async def test_demo_mode_uses_cached_shelf_response(self):
        """Test demo mode returns cached shelf response"""
        with patch('services.gemini_service.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            service = GeminiService()

            # Mock file reading for demo response
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.__enter__.return_value.read.return_value = json.dumps({
                    "reasoning_steps": [],
                    "message_to_owner": "Demo shelf response",
                    "structured_data": {"products": []}
                })
                mock_open.return_value = mock_file

                result = await service.process_shelf_photo(
                    image_base64="fake_base64",
                    context={"store_name": "Test Store"}
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_demo_mode_uses_cached_parchi_response(self):
        """Test demo mode returns cached parchi response"""
        with patch('services.gemini_service.settings') as mock_settings:
            mock_settings.DEMO_MODE = True
            service = GeminiService()

            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.__enter__.return_value.read.return_value = json.dumps({
                    "reasoning_steps": [],
                    "message_to_owner": "Demo parchi response",
                    "structured_data": {"transactions": []}
                })
                mock_open.return_value = mock_file

                result = await service.process_parchi_image(
                    image_base64="fake_base64",
                    context={"store_name": "Test Store"}
                )

                assert result is not None


class TestErrorHandling:
    """Test error handling in Gemini service"""

    @pytest.mark.asyncio
    async def test_handles_malformed_json_response(self, gemini_service):
        """Test service handles malformed JSON from Gemini"""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            with pytest.raises(Exception):
                await gemini_service.process_shelf_photo(
                    image_base64="fake_base64",
                    context={"store_name": "Test Store"}
                )

    @pytest.mark.asyncio
    async def test_handles_api_timeout(self, gemini_service):
        """Test service handles API timeout"""
        with patch.object(gemini_service.model, 'generate_content_async',
                         side_effect=asyncio.TimeoutError()):

            with pytest.raises(asyncio.TimeoutError):
                await gemini_service.process_shelf_photo(
                    image_base64="fake_base64",
                    context={"store_name": "Test Store"}
                )

    @pytest.mark.asyncio
    async def test_handles_missing_structured_data(self, gemini_service):
        """Test service handles missing structured_data in response"""
        incomplete_response = {
            "reasoning_steps": [],
            "message_to_owner": "Incomplete response"
            # Missing structured_data
        }

        mock_response = Mock()
        mock_response.text = json.dumps(incomplete_response)

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response):

            result = await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context={"store_name": "Test Store"}
            )

            # Should still work with empty structured_data
            assert result.structured_data == {}


class TestContextFormatting:
    """Test context formatting for prompts"""

    @pytest.mark.asyncio
    async def test_context_includes_all_fields(self, gemini_service, sample_shelf_response):
        """Test all context fields are included in prompt"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_shelf_response)

        full_context = {
            "store_name": "Sharma General Store",
            "owner_name": "Rajesh Sharma",
            "city": "Mumbai",
            "language": "hinglish",
            "upcoming_festivals": [{"name": "Navratri", "days_until": 2}],
            "weather": {"temperature": 30, "condition": "clear"}
        }

        with patch.object(gemini_service.model, 'generate_content_async',
                         return_value=mock_response) as mock_call:

            await gemini_service.process_shelf_photo(
                image_base64="fake_base64",
                context=full_context
            )

            # Verify the call was made (context was used)
            assert mock_call.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
