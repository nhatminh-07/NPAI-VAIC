"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /yield/predict
Response: YieldForecastResult
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.yield_service import predict_yield

router = APIRouter(prefix="/yield", tags=["Frontend - Yield Forecast"])


class YieldInput(BaseModel):
    cropType: str
    areaHa: float
    plantingDate: str  # ISO date string
    district: Optional[str] = "Điện Biên"


def _get_risk_level(predicted_yield: float) -> tuple[str, str]:
    """Calculate risk level based on predicted yield."""
    if predicted_yield >= 5.0:
        return "low", "Năng suất cao, điều kiện thuận lợi"
    elif predicted_yield >= 3.0:
        return "medium", "Năng suất trung bình, cần chú ý chăm sóc"
    else:
        return "high", "Năng suất thấp, cần cải thiện điều kiện canh tác"


def _get_rationale(crop_type: str, area_ha: float) -> List[str]:
    """Generate rationale notes."""
    rationale = [
        f"Dự báo dựa trên diện tích {area_ha} ha cây trồng {crop_type}",
        "Sử dụng dữ liệu thời tiết và lịch sử năng suất vụ trước",
    ]
    return rationale


@router.post("/predict")
async def predict_yield_frontend(input: YieldInput):
    """Frontend API: Dự báo năng suất (JSON body)."""
    try:
        sowing_date = date.fromisoformat(input.plantingDate)
    except ValueError:
        raise HTTPException(400, "Định dạng ngày không hợp lệ. Dùng ISO format: YYYY-MM-DD")

    try:
        result = predict_yield(
            crop_name=input.cropType,
            area_ha=input.areaHa,
            sowing_date=sowing_date,
        )
    except Exception as e:
        raise HTTPException(500, f"Lỗi dự báo năng suất: {e}")

    harvest_date = result["harvest_date"]
    predicted_yield_per_ha = result["predicted_yield_per_ha"]
    risk, risk_note = _get_risk_level(predicted_yield_per_ha)

    # Calculate harvest window (5 days before and after)
    window_start = harvest_date - timedelta(days=5)
    window_end = harvest_date + timedelta(days=5)

    return {
        "predictedYieldTPerHa": result["predicted_yield_per_ha"],
        "totalOutputTons": result["predicted_yield_tons"],
        "harvestWindowStart": window_start.isoformat(),
        "harvestWindowEnd": window_end.isoformat(),
        "confidence": 0.85,  # Placeholder confidence
        "risk": risk,
        "riskNote": risk_note,
        "rationale": _get_rationale(input.cropType, input.areaHa),
    }
