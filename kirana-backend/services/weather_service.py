"""
Weather service using OpenWeatherMap API
Provides current weather and forecast for demand prediction
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger

from config.settings import settings


class WeatherService:
    """Service for fetching weather data"""

    def __init__(self):
        """Initialize weather service"""
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache: Dict[str, tuple[Dict, datetime]] = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour

        logger.info("WeatherService initialized")

    async def get_current_weather(
        self,
        city: str,
        country: str = "IN"
    ) -> Dict[str, Any]:
        """
        Get current weather for a city

        Args:
            city: City name
            country: Country code (default: IN for India)

        Returns:
            Weather data dict
        """
        cache_key = f"{city},{country}"

        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                logger.debug(f"Using cached weather for {city}")
                return cached_data

        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": f"{city},{country}",
                "appid": self.api_key,
                "units": "metric"  # Celsius
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()

            data = response.json()

            # Parse relevant fields
            weather_data = {
                "temp_c": round(data["main"]["temp"], 1),
                "feels_like_c": round(data["main"]["feels_like"], 1),
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["main"].lower(),
                "description": data["weather"][0]["description"],
                "city": data["name"],
                "timestamp": datetime.now().isoformat()
            }

            # Cache the result
            self.cache[cache_key] = (weather_data, datetime.now())

            logger.success(
                f"Fetched weather for {city}: {weather_data['temp_c']}°C, "
                f"{weather_data['condition']}"
            )

            return weather_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather for {city}: {e}")
            # Return fallback data
            return self._get_fallback_weather(city)

        except Exception as e:
            logger.error(f"Error fetching weather for {city}: {e}")
            return self._get_fallback_weather(city)

    async def get_forecast(
        self,
        city: str,
        country: str = "IN",
        days: int = 5
    ) -> list[Dict[str, Any]]:
        """
        Get weather forecast for next N days

        Args:
            city: City name
            country: Country code
            days: Number of days (max 5 for free API)

        Returns:
            List of daily forecast dicts
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": f"{city},{country}",
                "appid": self.api_key,
                "units": "metric",
                "cnt": min(days * 8, 40)  # 8 data points per day, max 40
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()

            data = response.json()

            # Group by day and get daily summary
            daily_forecasts = []
            current_day = None
            day_data = []

            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                day = dt.date()

                if current_day != day:
                    # Process previous day
                    if day_data:
                        daily_forecasts.append(
                            self._summarize_day(current_day, day_data)
                        )
                        if len(daily_forecasts) >= days:
                            break

                    # Start new day
                    current_day = day
                    day_data = []

                day_data.append(item)

            # Process last day
            if day_data and len(daily_forecasts) < days:
                daily_forecasts.append(
                    self._summarize_day(current_day, day_data)
                )

            logger.success(f"Fetched {len(daily_forecasts)} day forecast for {city}")

            return daily_forecasts

        except Exception as e:
            logger.error(f"Error fetching forecast for {city}: {e}")
            # Return fallback forecast
            return self._get_fallback_forecast(city, days)

    def _summarize_day(
        self,
        date,
        data_points: list
    ) -> Dict[str, Any]:
        """
        Summarize multiple data points into daily forecast

        Args:
            date: Date of forecast
            data_points: List of 3-hour forecast data points

        Returns:
            Daily summary dict
        """
        temps = [item["main"]["temp"] for item in data_points]
        conditions = [item["weather"][0]["main"].lower() for item in data_points]

        # Most common condition
        condition = max(set(conditions), key=conditions.count)

        return {
            "date": str(date),
            "temp_min": round(min(temps), 1),
            "temp_max": round(max(temps), 1),
            "temp_avg": round(sum(temps) / len(temps), 1),
            "condition": condition,
            "rain_probability": any("rain" in c for c in conditions)
        }

    def _get_fallback_weather(self, city: str) -> Dict[str, Any]:
        """
        Get fallback weather data when API fails

        Args:
            city: City name

        Returns:
            Fallback weather dict
        """
        logger.warning(f"Using fallback weather for {city}")

        # Seasonal defaults for India
        month = datetime.now().month

        # Summer (Mar-Jun)
        if 3 <= month <= 6:
            temp = 35
            condition = "clear"
        # Monsoon (Jul-Sep)
        elif 7 <= month <= 9:
            temp = 28
            condition = "rain"
        # Winter (Nov-Feb)
        elif month >= 11 or month <= 2:
            temp = 18
            condition = "clear"
        # Autumn (Oct)
        else:
            temp = 25
            condition = "clear"

        return {
            "temp_c": temp,
            "feels_like_c": temp,
            "humidity": 60,
            "condition": condition,
            "description": f"Typical {condition} weather",
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }

    def _get_fallback_forecast(
        self,
        city: str,
        days: int
    ) -> list[Dict[str, Any]]:
        """
        Get fallback forecast when API fails

        Args:
            city: City name
            days: Number of days

        Returns:
            Fallback forecast list
        """
        logger.warning(f"Using fallback forecast for {city}")

        current_weather = self._get_fallback_weather(city)
        temp = current_weather["temp_c"]
        condition = current_weather["condition"]

        forecasts = []
        for i in range(days):
            date = datetime.now().date() + timedelta(days=i)
            forecasts.append({
                "date": str(date),
                "temp_min": temp - 3,
                "temp_max": temp + 3,
                "temp_avg": temp,
                "condition": condition,
                "rain_probability": condition == "rain",
                "fallback": True
            })

        return forecasts


# Singleton instance
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get or create WeatherService singleton"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
