"""
Yield Forecast Service - Dự báo năng suất dựa trên thời tiết thực tế.
Luồng:
1. Lấy thời tiết hiện tại từ Open-Meteo API
2. Đối chiếu với điều kiện lý tưởng của từng loại cây
3. Tính độ lệch và đưa ra dự báo
4. Khuyến cáo thu hoạch sớm/nорма/nếu thời tiết nguy hiểm
"""

from datetime import date, timedelta
from typing import Optional

from app.services.weather_service import get_current_weather, get_forecast_7d

# Thời tiết lý tưởng cho từng loại cây trồng
OPTIMAL_WEATHER = {
    "rice": {
        "name_vi": "Lúa",
        "name_en": "Rice",
        "growth_days": 110,
        "temp_min": 20.0,
        "temp_max": 30.0,
        "temp_optimal": 25.0,
        "rainfall_min": 150.0,
        "rainfall_max": 300.0,
        "rainfall_optimal": 200.0,
        "humidity_min": 70.0,
        "humidity_max": 85.0,
        "humidity_optimal": 78.0,
        "rain_tolerance": "high",  # Ưa nước, mưa nhiều không sao
        "notes": "Cây lúa ưa nước, cần tưới đều đặn. Mưa nhiều là điều kiện lý tưởng.",
    },
    "coffee": {
        "name_vi": "Cà phê",
        "name_en": "Coffee",
        "growth_days": 240,
        "temp_min": 15.0,
        "temp_max": 28.0,
        "temp_optimal": 22.0,
        "rainfall_min": 150.0,
        "rainfall_max": 250.0,
        "rainfall_optimal": 180.0,
        "humidity_min": 75.0,
        "humidity_max": 90.0,
        "humidity_optimal": 82.0,
        "rain_tolerance": "medium",  # Không thích nước đọng
        "notes": "Cà phê cần khí hậu mát mẻ, ẩm ướt. Không chịu được ngập úng.",
    },
    "vegetable": {
        "name_vi": "Rau màu",
        "name_en": "Vegetable",
        "growth_days": 65,
        "temp_min": 18.0,
        "temp_max": 30.0,
        "temp_optimal": 24.0,
        "rainfall_min": 80.0,
        "rainfall_max": 200.0,
        "rainfall_optimal": 120.0,
        "humidity_min": 60.0,
        "humidity_max": 80.0,
        "humidity_optimal": 70.0,
        "rain_tolerance": "low",  # Không chịu được ngập, cần thoát nước tốt
        "notes": "Rau màu cần đất thoát nước tốt. Ngập úng gây thối rễ.",
    },
}

# Tọa độ theo huyện Điện Biên (cho weather API)
DISTRICT_COORDS = {
    "Thành phố Điện Biên Phủ": (21.3865, 103.0231),
    "Huyện Tuần Giáo": (21.6167, 103.4333),
    "Huyện Mường Chà": (21.7000, 102.8833),
    "Huyện Tủa Chùa": (21.4833, 103.0833),
    "Huyện Mường Nhé": (21.9667, 102.4667),
    "Huyện Điện Biên Đông": (21.3667, 102.8167),
    "Huyện Mường Ảng": (21.5833, 103.1500),
    "Huyện Nậm Pồ": (21.8333, 102.7333),
}

DEFAULT_COORDS = (21.8, 103.0)  # Điện Biên center


def _get_coords(district: str) -> tuple[float, float]:
    """Lấy tọa độ từ tên huyện."""
    return DISTRICT_COORDS.get(district, DEFAULT_COORDS)


def _calculate_weather_deviation(current: dict, optimal: dict) -> dict:
    """Tính độ lệch thời tiết hiện tại so với lý tưởng."""
    temp = current.get("temperature", 25)
    humidity = current.get("humidity", 70)
    rainfall = current.get("precipitation", 0)

    # Độ lệch nhiệt độ
    temp_dev = abs(temp - optimal["temp_optimal"])
    if temp < optimal["temp_min"]:
        temp_status = "too_cold"
        temp_impact = -0.15
    elif temp > optimal["temp_max"]:
        temp_status = "too_hot"
        temp_impact = -0.20
    else:
        temp_status = "optimal"
        temp_impact = 0.0

    # Độ lệch độ ẩm
    if humidity < optimal["humidity_min"]:
        humidity_status = "too_dry"
        humidity_impact = -0.10
    elif humidity > optimal["humidity_max"]:
        humidity_status = "too_humid"
        humidity_impact = -0.05 if optimal["rain_tolerance"] == "high" else -0.15
    else:
        humidity_status = "optimal"
        humidity_impact = 0.05

    # Ảnh hưởng mưa
    rain_impact = 0.0
    if rainfall > 10:  # Mưa nhiều trong ngày
        if optimal["rain_tolerance"] == "high":
            rain_impact = 0.05  # Tốt cho lúa
        elif optimal["rain_tolerance"] == "medium":
            rain_impact = -0.05
        else:
            rain_impact = -0.15  # Xấu cho rau

    # Tổng impact
    total_impact = temp_impact + humidity_impact + rain_impact

    return {
        "temp": temp,
        "temp_dev": round(temp_dev, 1),
        "temp_status": temp_status,
        "humidity": humidity,
        "humidity_status": humidity_status,
        "rainfall": rainfall,
        "rain_impact": rain_impact,
        "total_impact": round(total_impact, 3),
    }


def _get_harvest_recommendation(
    deviation: dict,
    optimal: dict,
    current_weather: dict,
    days_since_planting: int,
    growth_days: int
) -> dict:
    """Đưa ra khuyến cáo thu hoạch dựa trên thời tiết."""
    remaining_days = growth_days - days_since_planting
    harvest_advice = "normal"
    advice_note = ""

    # Kiểm tra các điều kiện nguy hiểm
    danger_signs = []

    if deviation["temp_status"] == "too_hot":
        danger_signs.append(f"Nhiệt độ cao {deviation['temp']}°C (tối đa: {optimal['temp_max']}°C)")

    if deviation["humidity_status"] == "too_humid" and optimal["rain_tolerance"] != "high":
        danger_signs.append(f"Độ ẩm cao {deviation['humidity']}% - nguy cơ nấm bệnh")

    if deviation["rain_impact"] < -0.10:
        danger_signs.append("Mưa nhiều gây ngập úng, cần thoát nước gấp")

    # Quyết định thu hoạch
    if remaining_days <= 7 and deviation["total_impact"] < -0.20:
        harvest_advice = "harvest_early"
        advice_note = f"Khuyến cáo THU HOẠCH SỚM trong 5-7 ngày. Thời tiết bất lợi sẽ ảnh hưởng nghiêm trọng đến chất lượng."
    elif remaining_days <= 14 and deviation["total_impact"] < -0.15:
        harvest_advice = "prepare_harvest"
        advice_note = "Chuẩn bị thu hoạch sớm trong 2 tuần tới. Theo dõi thời tiết chặt chẽ."
    elif deviation["total_impact"] > 0:
        harvest_advice = "optimal"
        advice_note = "Điều kiện thời tiết thuận lợi cho cây trồng. Tiếp tục chăm sóc bình thường."
    elif danger_signs:
        harvest_advice = "monitor"
        advice_note = f"Cảnh báo: {'; '.join(danger_signs)}. Cần theo dõi thường xuyên."

    return {
        "harvest_advice": harvest_advice,
        "advice_note": advice_note,
        "remaining_days": max(0, remaining_days),
        "danger_signs": danger_signs,
    }


def _calculate_base_yield(crop_name: str, area_ha: float) -> float:
    """Tính năng suất cơ bản theo loại cây và diện tích."""
    base_yields = {
        "rice": 5.5,      # tấn/ha
        "coffee": 2.5,    # tấn/ha
        "vegetable": 12.0, # tấn/ha
    }
    return base_yields.get(crop_name, 5.0) * area_ha


def predict_yield(
    crop_name: str,
    area_ha: float,
    sowing_date: date,
    district: str = "Điện Biên",
) -> dict:
    """
    Dự báo năng suất dựa trên thời tiết thực tế.

    Args:
        crop_name: Loại cây (rice/coffee/vegetable)
        area_ha: Diện tích (ha)
        sowing_date: Ngày gieo trồng
        district: Tên huyện để lấy tọa độ thời tiết

    Returns:
        dict với dự báo năng suất, so sánh thời tiết, và khuyến cáo
    """
    # Validate crop
    if crop_name not in OPTIMAL_WEATHER:
        crop_name = "rice"

    optimal = OPTIMAL_WEATHER[crop_name]
    lat, lon = _get_coords(district)

    # Lấy thời tiết hiện tại
    current_weather = get_current_weather(lat=lat, lon=lon)

    # Lấy dự báo 7 ngày
    forecast = get_forecast_7d(lat=lat, lon=lon)

    # Tính độ lệch
    deviation = _calculate_weather_deviation(current_weather, optimal)

    # Tính số ngày đã trồng
    days_since_planting = (date.today() - sowing_date).days

    # Tính ngày thu hoạch dự kiến
    harvest_date = sowing_date + timedelta(days=optimal["growth_days"])

    # Tính năng suất với điều chỉnh thời tiết
    base_yield = _calculate_base_yield(crop_name, area_ha)
    adjusted_yield = base_yield * (1 + deviation["total_impact"])
    adjusted_yield_per_ha = adjusted_yield / area_ha if area_ha > 0 else 0

    # Khuyến cáo thu hoạch
    harvest_rec = _get_harvest_recommendation(
        deviation, optimal, current_weather, days_since_planting, optimal["growth_days"]
    )

    # Tính confidence dựa trên độ lệch thời tiết
    confidence = max(0.6, min(0.95, 0.85 - abs(deviation["total_impact"]) * 0.5))

    # Risk level
    if deviation["total_impact"] >= -0.05:
        risk = "low"
        risk_note = "Điều kiện thời tiết thuận lợi cho cây trồng."
    elif deviation["total_impact"] >= -0.15:
        risk = "medium"
        risk_note = "Thời tiết có độ lệch nhẹ, cần theo dõi."
    else:
        risk = "high"
        risk_note = "Thời tiết bất lợi, có nguy cơ ảnh hưởng đến năng suất."

    # So sánh vs điều kiện lý tưởng
    comparison = {
        "current": {
            "temperature": deviation["temp"],
            "humidity": deviation["humidity"],
            "rainfall": deviation["rainfall"],
            "description": current_weather.get("weather_description", ""),
        },
        "optimal": {
            "temperature": f"{optimal['temp_min']}-{optimal['temp_max']}°C",
            "humidity": f"{optimal['humidity_min']}-{optimal['humidity_max']}%",
            "rainfall": f"{optimal['rainfall_min']}-{optimal['rainfall_max']}mm",
        },
        "deviation": {
            "temperature": f"{'+' if deviation['temp'] >= optimal['temp_optimal'] else ''}{round(deviation['temp'] - optimal['temp_optimal'], 1)}°C",
            "status": deviation["temp_status"],
        },
    }

    return {
        # Yield prediction
        "predicted_yield_tons": round(max(0, adjusted_yield), 2),
        "predicted_yield_per_ha": round(max(0, adjusted_yield_per_ha), 2),
        "base_yield_per_ha": optimal["name_vi"],
        "harvest_date": harvest_date,
        "confidence": round(confidence, 2),

        # Weather analysis
        "current_weather": current_weather,
        "weather_comparison": comparison,
        "weather_deviation_pct": round(deviation["total_impact"] * 100, 1),

        # Crop info
        "crop_info": {
            "name_vi": optimal["name_vi"],
            "growth_days": optimal["growth_days"],
            "days_since_planting": days_since_planting,
            "notes": optimal["notes"],
        },

        # Harvest recommendation
        "harvest": harvest_rec,

        # Risk assessment
        "risk": risk,
        "risk_note": risk_note,
    }
