from datetime import date, timedelta

import joblib
import pandas as pd

from app.config import YIELD_MODEL_PATH, SAMPLE_YIELD_CSV

# Số ngày sinh trưởng ước tính theo loại cây (để tính thời điểm thu hoạch)
GROWTH_DAYS = {"rice": 110, "coffee": 240, "vegetable": 65}

_artifact = None


def _load_artifact():
    global _artifact
    if _artifact is None:
        _artifact = joblib.load(YIELD_MODEL_PATH)
    return _artifact


def _fallback_weather(crop_name: str) -> tuple[float, float]:
    """Nếu người dùng không nhập thời tiết, lấy trung bình từ dữ liệu mẫu theo cây trồng."""
    df = pd.read_csv(SAMPLE_YIELD_CSV)
    subset = df[df["crop_name"] == crop_name]
    return float(subset["avg_temperature"].mean()), float(subset["total_rainfall"].mean())


def _fallback_prev_yield(crop_name: str) -> float:
    df = pd.read_csv(SAMPLE_YIELD_CSV)
    subset = df[df["crop_name"] == crop_name]
    return float(subset["prev_season_yield"].mean())


def predict_yield(
    crop_name: str,
    area_ha: float,
    sowing_date: date,
    avg_temperature: float | None = None,
    total_rainfall: float | None = None,
    prev_season_yield: float | None = None,
) -> dict:
    artifact = _load_artifact()
    model = artifact["model"]
    crop_code_map = artifact["crop_code_map"]

    if crop_name not in crop_code_map:
        crop_name = "rice"  # mặc định an toàn cho MVP nếu nhận giá trị lạ

    if avg_temperature is None or total_rainfall is None:
        fb_temp, fb_rain = _fallback_weather(crop_name)
        avg_temperature = avg_temperature if avg_temperature is not None else fb_temp
        total_rainfall = total_rainfall if total_rainfall is not None else fb_rain

    if prev_season_yield is None:
        prev_season_yield = _fallback_prev_yield(crop_name)

    features = pd.DataFrame([{
        "crop_code": crop_code_map[crop_name],
        "area_ha": area_ha,
        "avg_temperature": avg_temperature,
        "total_rainfall": total_rainfall,
        "prev_season_yield": prev_season_yield,
    }])

    yield_per_ha = float(model.predict(features)[0])
    total_yield = round(yield_per_ha * area_ha, 2)

    growth_days = GROWTH_DAYS.get(crop_name, 100)
    harvest_date = sowing_date + timedelta(days=growth_days)

    quarter = (harvest_date.month - 1) // 3 + 1
    season_label = f"{harvest_date.year}-Q{quarter}"

    notes = (
        f"Dự đoán dựa trên diện tích {area_ha} ha, nhiệt độ TB {avg_temperature:.1f}°C, "
        f"tổng lượng mưa {total_rainfall:.0f}mm. Độ chính xác sẽ cải thiện khi có dữ liệu "
        f"lịch sử thực tế thay cho dữ liệu mẫu."
    )

    return {
        "predicted_yield_tons": total_yield,
        "predicted_yield_per_ha": round(yield_per_ha, 3),
        "harvest_date": harvest_date,
        "season": season_label,
        "notes": notes,
    }
