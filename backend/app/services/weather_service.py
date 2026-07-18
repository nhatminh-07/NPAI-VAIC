"""
Weather Service - Tích hợp Open-Meteo API (free, no API key required).
https://open-meteo.com/
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import requests

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"

# Cache for weather data (5 min TTL)
_weather_cache: dict = {}
_CACHE_TTL = 300  # seconds


def get_current_weather(lat: float = 21.8, lon: float = 103.0) -> dict:
    """
    Lấy thời tiết hiện tại cho vĩ độ/kinh độ.
    Mặc định: Điện Biên (21.8°N, 103.0°E)

    Args:
        lat: Vĩ độ
        lon: Kinh độ

    Returns:
        dict với thông tin thời tiết
    """
    cache_key = f"{lat:.2f}_{lon:.2f}"
    now = datetime.now().timestamp()

    # Check cache
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if now - cached_time < _CACHE_TTL:
            return cached_data

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "precipitation",
                "weather_code", "wind_speed_10m", "soil_temperature_0cm",
            ],
            "timezone": "Asia/Ho_Chi_Minh",
        }
        resp = requests.get(f"{OPEN_METEO_BASE}/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        weather_code = current.get("weather_code", 0)

        result = {
            "temperature": round(current.get("temperature_2m", 25), 1),
            "humidity": round(current.get("relative_humidity_2m", 70), 1),
            "precipitation": round(current.get("precipitation", 0), 1),
            "wind_speed": round(current.get("wind_speed_10m", 5), 1),
            "soil_temperature": round(current.get("soil_temperature_0cm", 26), 1),
            "weather_description": _weather_code_to_desc(weather_code),
            "weather_icon": _weather_code_to_icon(weather_code),
            "location": f"{lat:.2f}°N, {lon:.2f}°E",
        }

        _weather_cache[cache_key] = (result, now)
        return result

    except Exception as e:
        print(f"[WeatherService] Error fetching weather: {e}")
        return _default_weather()


def get_forecast_7d(lat: float = 21.8, lon: float = 103.0) -> dict:
    """
    Lấy dự báo thời tiết 7 ngày.

    Args:
        lat: Vĩ độ
        lon: Kinh độ

    Returns:
        dict với forecast 7 ngày
    """
    cache_key = f"forecast_{lat:.2f}_{lon:.2f}"
    now = datetime.now().timestamp()

    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if now - cached_time < _CACHE_TTL * 3:  # 15 min TTL for forecast
            return cached_data

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "wind_speed_10m_max",
            ],
            "timezone": "Asia/Ho_Chi_Minh",
            "forecast_days": 7,
        }
        resp = requests.get(f"{OPEN_METEO_BASE}/forecast", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecasts = []

        for i, date in enumerate(dates):
            wc = daily.get("weather_code", [0])[i] if isinstance(daily.get("weather_code"), list) else 0
            forecasts.append({
                "date": date,
                "weather_description": _weather_code_to_desc(
                    daily.get("weather_code", [0])[i] if isinstance(daily.get("weather_code"), list) else 0
                ),
                "weather_icon": _weather_code_to_icon(
                    daily.get("weather_code", [0])[i] if isinstance(daily.get("weather_code"), list) else 0
                ),
                "temp_max": round(daily.get("temperature_2m_max", [30])[i] if isinstance(daily.get("temperature_2m_max"), list) else 30, 1),
                "temp_min": round(daily.get("temperature_2m_min", [20])[i] if isinstance(daily.get("temperature_2m_min"), list) else 20, 1),
                "precipitation": round(daily.get("precipitation_sum", [0])[i] if isinstance(daily.get("precipitation_sum"), list) else 0, 1),
                "wind_max": round(daily.get("wind_speed_10m_max", [10])[i] if isinstance(daily.get("wind_speed_10m_max"), list) else 10, 1),
            })

        result = {
            "location": f"{lat:.2f}°N, {lon:.2f}°E",
            "forecast": forecasts,
        }

        _weather_cache[cache_key] = (result, now)
        return result

    except Exception as e:
        print(f"[WeatherService] Error fetching forecast: {e}")
        return {"location": f"{lat:.2f}°N, {lon:.2f}°E", "forecast": []}


def _weather_code_to_desc(code: int) -> str:
    """Map WMO weather code -> description."""
    mapping = {
        0: "Trời quang",
        1: "Ít mây",
        2: "Nhiều mây",
        3: "U ám",
        45: "Sương mù",
        48: "Sương mù đóng băng",
        51: "Mưa phùn nhẹ",
        53: "Mưa phùn vừa",
        55: "Mưa phùn nặng",
        61: "Mưa nhẹ",
        63: "Mưa vừa",
        65: "Mưa to",
        71: "Tuyết nhẹ",
        73: "Tuyết vừa",
        75: "Tuyết to",
        77: "Hạt tuyết",
        80: "Mưa rào nhẹ",
        81: "Mưa rào vừa",
        82: "Mưa rào to",
        85: "Mưa tuyết nhẹ",
        86: "Mưa tuyết to",
        95: "Dông",
        96: "Dông kèm mưa đá nhẹ",
        99: "Dông kèm mưa đá nặng",
    }
    return mapping.get(code, f"Code {code}")


def _weather_code_to_icon(code: int) -> str:
    """Map WMO weather code -> icon name."""
    if code == 0:
        return "sun"
    elif code in [1, 2, 3]:
        return "cloud"
    elif code in [45, 48]:
        return "cloud-fog"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "cloud-rain"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "cloud-snow"
    elif code >= 95:
        return "cloud-lightning"
    return "cloud"


def _default_weather() -> dict:
    """Fallback weather data when API fails."""
    return {
        "temperature": 26.0,
        "humidity": 75.0,
        "precipitation": 0.0,
        "wind_speed": 5.0,
        "soil_temperature": 27.0,
        "weather_description": "Không rõ (offline)",
        "weather_icon": "cloud",
        "location": "Điện Biên",
    }
