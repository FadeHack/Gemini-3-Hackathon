"""
Test script to validate configuration
"""

from config.settings import settings
from config import constants
from config.system_prompt import get_prompt, PROMPTS


def test_settings():
    """Test settings loading"""
    print("Testing Settings...")

    # Check API keys are loaded
    assert settings.GEMINI_API_KEY, "Gemini API key not loaded"
    assert settings.WEATHER_API_KEY, "Weather API key not loaded"
    print(f"  ✅ Settings loaded: {settings}")

    # Check paths
    assert settings.PRODUCT_CATALOG_PATH == "./data/products.json"
    print(f"  ✅ Data paths configured")

    # Check CORS origins
    origins = settings.allowed_origins_list
    assert len(origins) >= 1
    print(f"  ✅ CORS origins: {origins}")

    # Check production mode
    is_prod = settings.is_production
    print(f"  ✅ Production mode: {is_prod}")


def test_constants():
    """Test constants and enums"""
    print("\nTesting Constants...")

    # Test enums
    assert constants.MessageType.TEXT == "text"
    assert constants.StockStatus.CRITICAL == "critical"
    assert constants.Urgency.HIGH == "high"
    print("  ✅ Enums defined correctly")

    # Test festival multipliers
    assert "diwali" in constants.FESTIVAL_MULTIPLIERS
    assert "navratri" in constants.FESTIVAL_MULTIPLIERS
    diwali_mult = constants.FESTIVAL_MULTIPLIERS["diwali"]
    assert diwali_mult["sweets"] == 4.0
    assert diwali_mult["pooja_items"] == 5.0
    print(f"  ✅ Festival multipliers loaded ({len(constants.FESTIVAL_MULTIPLIERS)} festivals)")

    # Test weather multipliers
    beverages_mult = constants.get_weather_multiplier("beverages", 36, "clear")
    assert beverages_mult == 1.4  # Hot weather
    print(f"  ✅ Weather multiplier (36°C beverages): {beverages_mult}x")

    instant_food_rain = constants.get_weather_multiplier("instant_food", 25, "rain")
    assert instant_food_rain == 1.3  # Rainy day
    print(f"  ✅ Weather multiplier (rain instant_food): {instant_food_rain}x")

    # Test day of week multipliers
    sunday_mult = constants.get_dow_multiplier("snacks", "Sunday")
    assert sunday_mult == 1.4  # Sunday snacks boost
    print(f"  ✅ Day-of-week multiplier (Sunday snacks): {sunday_mult}x")

    # Test stock thresholds
    assert constants.STOCK_THRESHOLDS["critical_days"] == 1.0
    assert constants.STOCK_THRESHOLDS["warning_days"] == 3.0
    print("  ✅ Stock thresholds configured")

    # Test reasoning step icons
    shelf_icon = constants.REASONING_STEP_ICONS[constants.ReasoningStepType.SHELF_ANALYSIS]
    assert shelf_icon == "🔍"
    print(f"  ✅ Reasoning step icons: {len(constants.REASONING_STEP_ICONS)} types")


def test_system_prompts():
    """Test system prompts"""
    print("\nTesting System Prompts...")

    # Test prompt registry
    assert len(PROMPTS) == 5
    assert "shelf_photo" in PROMPTS
    assert "parchi_reading" in PROMPTS
    assert "voice_message" in PROMPTS
    print(f"  ✅ {len(PROMPTS)} prompt types registered")

    # Test prompt generation with context
    context = {
        "store_name": "Sharma General Store",
        "owner_name": "Rajesh",
        "city": "Indore",
        "language": "hinglish",
        "upcoming_festivals": [
            {"name": "Navratri", "start_date": "2026-02-16"}
        ],
        "weather": {"temp_c": 32}
    }

    # Test shelf photo prompt
    shelf_prompt = get_prompt("shelf_photo", context)
    assert "Rajesh" in shelf_prompt
    assert "Navratri" in shelf_prompt
    assert "hinglish" in shelf_prompt
    assert len(shelf_prompt) > 500  # Should be detailed
    print(f"  ✅ Shelf photo prompt: {len(shelf_prompt)} chars")

    # Test parchi reading prompt
    parchi_prompt = get_prompt("parchi_reading", context)
    assert "kacchi parchi" in parchi_prompt
    assert "Rajesh" in parchi_prompt
    assert len(parchi_prompt) > 400
    print(f"  ✅ Parchi reading prompt: {len(parchi_prompt)} chars")

    # Test voice message prompt
    voice_prompt = get_prompt("voice_message", context)
    assert "voice" in voice_prompt.lower()
    assert "Rajesh" in voice_prompt
    assert len(voice_prompt) > 400
    print(f"  ✅ Voice message prompt: {len(voice_prompt)} chars")

    # Test general query prompt
    general_prompt = get_prompt("general_query", context)
    assert "KiranaGPT" in general_prompt
    assert len(general_prompt) > 300
    print(f"  ✅ General query prompt: {len(general_prompt)} chars")

    # Test demand forecast prompt
    forecast_prompt = get_prompt("demand_forecast", context)
    assert "forecast" in forecast_prompt.lower()
    assert "Navratri" in forecast_prompt or "festival" in forecast_prompt.lower()
    assert len(forecast_prompt) > 400
    print(f"  ✅ Demand forecast prompt: {len(forecast_prompt)} chars")

    # Test invalid prompt type
    try:
        get_prompt("invalid_type", context)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown prompt type" in str(e)
        print("  ✅ Invalid prompt type raises error correctly")


def main():
    print("=" * 60)
    print("KiranaGPT Backend - Configuration Validation")
    print("=" * 60)
    print()

    try:
        test_settings()
        test_constants()
        test_system_prompts()

        print()
        print("=" * 60)
        print("✅ All configuration tests passed!")
        print("=" * 60)
        print()
        print("Configuration Summary:")
        print(f"  • Gemini API: {'Configured' if settings.GEMINI_API_KEY else 'Missing'}")
        print(f"  • Weather API: {'Configured' if settings.WEATHER_API_KEY else 'Missing'}")
        print(f"  • Festivals: {len(constants.FESTIVAL_MULTIPLIERS)} configured")
        print(f"  • System prompts: {len(PROMPTS)} types")
        print(f"  • Debug mode: {settings.DEBUG}")
        print(f"  • Demo mode: {settings.DEMO_MODE}")
        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Configuration test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
