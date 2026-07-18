"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /yield/predict
Response: YieldForecastResult

Luồng:
1. Lấy thời tiết hiện tại từ Open-Meteo API
2. Đối chiếu với điều kiện lý tưởng của từng loại cây (từ dataset dien_bien_crops_ml.csv)
3. Tính độ lệch và đưa ra dự báo năng suất
4. Khuyến cáo thu hoạch sớm/nорма/nếu nguy hiểm
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.yield_service import predict_yield

router = APIRouter(prefix="/yield", tags=["Frontend - Yield Forecast"])


class YieldInput(BaseModel):
    cropType: str  # rice | coffee | vegetable
    areaHa: float
    plantingDate: str  # ISO date string: YYYY-MM-DD
    district: Optional[str] = "Thành phố Điện Biên Phủ"
    season: Optional[str] = None  # xuân, mùa, đông, chiêm (optional)


@router.post("/predict")
async def predict_yield_frontend(input: YieldInput):
    """
    Frontend API: Dự báo năng suất dựa trên thời tiết thực tế.
    - Lấy thời tiết hiện tại từ Open-Meteo API
    - So sánh với điều kiện lý tưởng của từng loại cây (từ dataset Điện Biên)
    - Đưa ra dự báo năng suất có điều chỉnh
    - Khuyến cáo thu hoạch sớm/nорма/nếu nguy hiểm
    """
    try:
        sowing_date = date.fromisoformat(input.plantingDate)
    except ValueError:
        raise HTTPException(400, "Định dạng ngày không hợp lệ. Dùng ISO format: YYYY-MM-DD")

    if input.areaHa <= 0:
        raise HTTPException(400, "Diện tích phải lớn hơn 0")

    try:
        result = predict_yield(
            crop_name=input.cropType,
            area_ha=input.areaHa,
            sowing_date=sowing_date,
            district=input.district or "Thành phố Điện Biên Phủ",
            season=input.season,
        )
    except Exception as e:
        raise HTTPException(500, f"Lỗi dự báo năng suất: {e}")

    harvest_date = result["harvest_date"]
    harvest_rec = result["harvest"]

    # Tạo harvest window
    if harvest_rec["harvest_advice"] == "harvest_early":
        window_start = date.today()
        window_end = window_start + timedelta(days=7)
    elif harvest_rec["harvest_advice"] == "prepare_harvest":
        window_start = date.today()
        window_end = date.today() + timedelta(days=14)
    else:
        window_start = harvest_date - timedelta(days=5)
        window_end = harvest_date + timedelta(days=5)

    # Generate rationale
    rationale = [
        f"Diện tích {input.areaHa} ha cây {result['crop_info']['name_vi']}",
        f"Ngày gieo: {input.plantingDate}, đã trồng {result['crop_info']['days_since_planting']} ngày",
        f"Thời tiết hiện tại: {result['current_weather']['weather_description']}, {result['current_weather']['temperature']}°C, {result['current_weather']['humidity']}%",
        f"Độ lệch so với lý tưởng: {result['weather_deviation_pct']}%",
    ]

    if harvest_rec["advice_note"]:
        rationale.append(harvest_rec["advice_note"])

    return {
        "predictedYieldTPerHa": result["predicted_yield_per_ha"],
        "totalOutputTons": result["predicted_yield_tons"],
        "yieldRange": result["yield_range"],
        "baseYieldPerHa": result["base_yield_per_ha"],
        "harvestWindowStart": window_start.isoformat(),
        "harvestWindowEnd": window_end.isoformat(),
        "confidence": result["confidence"],
        "risk": result["risk"],
        "riskNote": result["risk_note"],
        "rationale": rationale,

        # Extended info
        "currentWeather": result["current_weather"],
        "weatherComparison": result["weather_comparison"],
        "harvestAdvice": harvest_rec["harvest_advice"],
        "harvestAdviceNote": harvest_rec["advice_note"],
        "remainingDays": harvest_rec["remaining_days"],
        "cropInfo": result["crop_info"],
    }
