"""
Yield Forecast Service - Dự báo năng suất dựa trên thời tiết thực tế.
Luồng:
1. Lấy thời tiết hiện tại từ Open-Meteo API
2. Đối chiếu với điều kiện lý tưởng của từng loại cây (từ dataset dien_bien_crops_ml.csv)
3. Tính độ lệch và đưa ra dự báo
4. Khuyến cáo thu hoạch sớm/nорма/nếu thời tiết nguy hiểm
"""

from datetime import date, timedelta
from typing import Optional

import pandas as pd

from app.config import BASE_DIR
from app.services.weather_service import get_current_weather, get_forecast_7d

# Đường dẫn dataset
CROPS_DATA_PATH = f"{BASE_DIR}/app/data/dien_bien_crops_ml.csv"

# Cache dataset
_crops_df = None


def _load_crops_data() -> pd.DataFrame:
    """Load dataset cây trồng Điện Biên."""
    global _crops_df
    if _crops_df is None:
        try:
            _crops_df = pd.read_csv(CROPS_DATA_PATH)
        except Exception as e:
            print(f"[YieldService] Warning: Cannot load crops data: {e}")
            _crops_df = pd.DataFrame()
    return _crops_df


# Map tên crop trong dataset -> crop type cho hệ thống
CROP_TYPE_MAP = {
    "Bắc Thơm số 7": "rice",
    "Séng Cù": "rice",
    "IR64": "rice",
    "Cà phê": "coffee",
    "Cà chua": "vegetable",
}

# Tọa độ theo huyện Điện Biên (hỗ trợ cả tên viết tắt từ frontend và tên đầy đủ)
DISTRICT_COORDS = {
    # Tên đầy đủ
    "Thành phố Điện Biên Phủ": (21.3865, 103.0231),
    "Huyện Tuần Giáo": (21.6167, 103.4333),
    "Huyện Mường Chà": (21.7000, 102.8833),
    "Huyện Tủa Chùa": (21.4833, 103.0833),
    "Huyện Mường Nhé": (21.9667, 102.4667),
    "Huyện Điện Biên Đông": (21.3667, 102.8167),
    "Huyện Mường Ảng": (21.5833, 103.1500),
    "Huyện Nậm Pồ": (21.8333, 102.7333),
    # Tên viết tắt (theo frontend/src/constants/districts.ts, dùng bởi hệ thống vùng canh tác)
    "Điện Biên": (21.3865, 103.0231),
    "Điện Biên Đông": (21.3667, 102.8167),
    "Mường Ảng": (21.5833, 103.1500),
    "Mường Chà": (21.7000, 102.8833),
    "Mường Nhé": (21.9667, 102.4667),
    "Nậm Pồ": (21.8333, 102.7333),
    "Tủa Chùa": (21.4833, 103.0833),
    "Tuần Giáo": (21.6167, 103.4333),
}

DEFAULT_COORDS = (21.8, 103.0)


def _get_coords(district: str) -> tuple[float, float]:
    """Lấy tọa độ từ tên huyện."""
    return DISTRICT_COORDS.get(district, DEFAULT_COORDS)


def _get_crop_info_from_dataset(crop_type: str, season: str = None) -> dict:
    """Lấy thông tin cây trồng từ dataset."""
    df = _load_crops_data()
    if df.empty:
        return _get_default_crop_info(crop_type)

    # Filter theo crop type
    crop_name_map = {v: k for k, v in CROP_TYPE_MAP.items()}
    if crop_type in crop_name_map:
        df = df[df["crop"] == crop_name_map[crop_type]]

    if season and not df.empty:
        # Filter theo mùa
        df_season = df[df["season"] == season]
        if not df_season.empty:
            df = df_season

    if df.empty:
        return _get_default_crop_info(crop_type)

    row = df.iloc[0]

    return {
        "name": row.get("crop", crop_type),
        "season": row.get("season", "unknown"),
        "growth_days_min": int(row.get("growth_days_min", 100)),
        "growth_days_max": int(row.get("growth_days_max", 120)),
        "temp_min": float(row.get("temp_c_min", 20)),
        "temp_max": float(row.get("temp_c_max", 30)),
        "temp_optimal": (float(row.get("temp_c_min", 20)) + float(row.get("temp_c_max", 30))) / 2,
        "humidity_min": float(row.get("humidity_pct_min", 70)),
        "humidity_max": float(row.get("humidity_pct_max", 90)),
        "humidity_optimal": (float(row.get("humidity_pct_min", 70)) + float(row.get("humidity_pct_max", 90))) / 2,
        "rainfall_min": float(row.get("rainfall_mm_min", 1000)),
        "rainfall_max": float(row.get("rainfall_mm_max", 2000)),
        "rainfall_optimal": (float(row.get("rainfall_mm_min", 1000)) + float(row.get("rainfall_mm_max", 2000))) / 2,
        "pH_min": float(row.get("soil_ph_min", 5.5)),
        "pH_max": float(row.get("soil_ph_max", 7.5)),
        "yield_min": float(row.get("yield_ton_ha_min", 5.0)),
        "yield_max": float(row.get("yield_ton_ha_max", 6.0)),
        "altitude_min": row.get("altitude_m_min"),
        "altitude_max": row.get("altitude_m_max"),
    }


def _get_default_crop_info(crop_type: str) -> dict:
    """Fallback info nếu không load được dataset."""
    defaults = {
        "rice": {
            "name": "Lúa",
            "season": "xuân/mùa",
            "growth_days_min": 100,
            "growth_days_max": 140,
            "temp_min": 20.0,
            "temp_max": 30.0,
            "temp_optimal": 25.0,
            "humidity_min": 70.0,
            "humidity_max": 90.0,
            "humidity_optimal": 80.0,
            "rainfall_min": 1200.0,
            "rainfall_max": 1800.0,
            "rainfall_optimal": 1500.0,
            "yield_min": 5.0,
            "yield_max": 6.5,
        },
        "coffee": {
            "name": "Cà phê",
            "season": "quanh năm",
            "growth_days_min": 720,
            "growth_days_max": 1440,
            "temp_min": 18.0,
            "temp_max": 25.0,
            "temp_optimal": 22.0,
            "humidity_min": 60.0,
            "humidity_max": 70.0,
            "humidity_optimal": 65.0,
            "rainfall_min": 1500.0,
            "rainfall_max": 2500.0,
            "rainfall_optimal": 2000.0,
            "yield_min": 2.5,
            "yield_max": 3.5,
        },
        "vegetable": {
            "name": "Rau màu",
            "season": "đông xuân",
            "growth_days_min": 65,
            "growth_days_max": 120,
            "temp_min": 18.0,
            "temp_max": 29.0,
            "temp_optimal": 24.0,
            "humidity_min": 60.0,
            "humidity_max": 70.0,
            "humidity_optimal": 65.0,
            "rainfall_min": 800.0,
            "rainfall_max": 1500.0,
            "rainfall_optimal": 1000.0,
            "yield_min": 10.0,
            "yield_max": 70.0,
        },
    }
    return defaults.get(crop_type, defaults["rice"])


def _calculate_weather_deviation(current: dict, optimal: dict) -> dict:
    """Tính độ lệch thời tiết hiện tại so với lý tưởng."""
    temp = current.get("temperature", 25)
    humidity = current.get("humidity", 70)
    rainfall = current.get("precipitation", 0)

    # Độ lệch nhiệt độ
    temp_dev = abs(temp - optimal["temp_optimal"])
    if temp < optimal["temp_min"]:
        temp_status = "too_cold"
        temp_impact = -0.15 * (optimal["temp_min"] - temp) / 5
    elif temp > optimal["temp_max"]:
        temp_status = "too_hot"
        temp_impact = -0.20 * (temp - optimal["temp_max"]) / 5
    else:
        temp_status = "optimal"
        temp_impact = 0.0

    # Độ lệch độ ẩm
    if humidity < optimal["humidity_min"]:
        humidity_status = "too_dry"
        humidity_impact = -0.10 * (optimal["humidity_min"] - humidity) / 10
    elif humidity > optimal["humidity_max"]:
        humidity_status = "too_humid"
        humidity_impact = -0.10
    else:
        humidity_status = "optimal"
        humidity_impact = 0.05

    # Ảnh hưởng mưa trong ngày (cần context về tổng lượng mưa theo mùa)
    rain_impact = 0.0
    crop_type = optimal.get("name", "").lower()

    if "lúa" in crop_type or "rice" in str(optimal):
        # Lúa ưa nước
        if rainfall > 20:
            rain_impact = 0.05
        elif rainfall > 5:
            rain_impact = 0.02
    elif "cà phê" in crop_type or "coffee" in str(optimal):
        # Cà phê không thích ngập
        if rainfall > 30:
            rain_impact = -0.10
        elif rainfall > 10:
            rain_impact = -0.02
    else:
        # Rau cần thoát nước
        if rainfall > 15:
            rain_impact = -0.12
        elif rainfall > 5:
            rain_impact = -0.03

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
        "total_impact": round(max(-0.5, min(0.3, total_impact)), 3),
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
    elif deviation["temp_status"] == "too_cold":
        danger_signs.append(f"Nhiệt độ thấp {deviation['temp']}°C (tối thiểu: {optimal['temp_min']}°C)")

    if deviation["humidity_status"] == "too_humid":
        danger_signs.append(f"Độ ẩm cao {deviation['humidity']}%")

    if deviation["rain_impact"] < -0.08:
        danger_signs.append("Mưa nhiều gây ngập úng, cần thoát nước gấp")

    # Quyết định thu hoạch
    if remaining_days <= 7 and deviation["total_impact"] < -0.20:
        harvest_advice = "harvest_early"
        advice_note = "Khuyến cáo THU HOẠCH SỚM trong 5-7 ngày. Thời tiết bất lợi ảnh hưởng nghiêm trọng."
    elif remaining_days <= 14 and deviation["total_impact"] < -0.15:
        harvest_advice = "prepare_harvest"
        advice_note = "Chuẩn bị thu hoạch sớm trong 2 tuần. Theo dõi thời tiết chặt chẽ."
    elif deviation["total_impact"] > 0.05:
        harvest_advice = "optimal"
        advice_note = "Điều kiện thời tiết thuận lợi. Tiếp tục chăm sóc bình thường."
    elif danger_signs:
        harvest_advice = "monitor"
        advice_note = f"Cảnh báo: {'; '.join(danger_signs)}. Cần theo dõi thường xuyên."

    return {
        "harvest_advice": harvest_advice,
        "advice_note": advice_note,
        "remaining_days": max(0, remaining_days),
        "danger_signs": danger_signs,
    }


def predict_yield(
    crop_name: str,
    area_ha: float,
    sowing_date: date,
    district: str = "Thành phố Điện Biên Phủ",
    season: str = None,
) -> dict:
    """
    Dự báo năng suất dựa trên thời tiết thực tế + dataset Điện Biên.

    Args:
        crop_name: Loại cây (rice/coffee/vegetable)
        area_ha: Diện tích (ha)
        sowing_date: Ngày gieo trồng
        district: Tên huyện để lấy tọa độ thời tiết
        season: Mùa vụ (xuân, mùa, đông, chiêm) - optional

    Returns:
        dict với dự báo năng suất, so sánh thời tiết, và khuyến cáo
    """
    # Lấy thông tin cây trồng từ dataset
    optimal = _get_crop_info_from_dataset(crop_name, season)
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
    growth_days_avg = (optimal["growth_days_min"] + optimal["growth_days_max"]) // 2
    harvest_date = sowing_date + timedelta(days=growth_days_avg)

    # Tính năng suất với điều chỉnh thời tiết
    base_yield = (optimal["yield_min"] + optimal["yield_max"]) / 2
    adjusted_yield_per_ha = base_yield * (1 + deviation["total_impact"])
    total_yield = adjusted_yield_per_ha * area_ha

    # Khuyến cáo thu hoạch
    harvest_rec = _get_harvest_recommendation(
        deviation, optimal, current_weather, days_since_planting, growth_days_avg
    )

    # Confidence dựa trên độ lệch
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

    # Crop info for frontend
    crop_info = {
        "name_vi": optimal["name"],
        "season": optimal["season"],
        "growth_days_min": optimal["growth_days_min"],
        "growth_days_max": optimal["growth_days_max"],
        "days_since_planting": days_since_planting,
        "yield_range": f"{optimal['yield_min']}-{optimal['yield_max']} tấn/ha",
    }

    return {
        # Yield prediction
        "predicted_yield_tons": round(max(0, total_yield), 2),
        "predicted_yield_per_ha": round(max(0, adjusted_yield_per_ha), 2),
        "base_yield_per_ha": round(base_yield, 2),
        "yield_range": f"{optimal['yield_min']}-{optimal['yield_max']} tấn/ha",
        "harvest_date": harvest_date,
        "confidence": round(confidence, 2),

        # Weather analysis
        "current_weather": current_weather,
        "weather_comparison": comparison,
        "weather_deviation_pct": round(deviation["total_impact"] * 100, 1),

        # Crop info
        "crop_info": crop_info,

        # Harvest recommendation
        "harvest": harvest_rec,

        # Risk assessment
        "risk": risk,
        "risk_note": risk_note,
    }