"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: GET /dashboard
Response: DashboardResult
"""
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="", tags=["Frontend - Dashboard"])

# Map frontend crop ID to backend crop name
CROP_ID_TO_NAME = {
    1: "rice",
    2: "coffee",
    3: "vegetable",
}


@router.get("/dashboard")
async def get_dashboard_frontend(
    period: str = Query("quarter", pattern="^(quarter|year)$"),
    cropId: Optional[int] = Query(None, description="1=rice, 2=coffee, 3=vegetable"),
):
    """Frontend API: Dashboard so sánh kỳ."""
    crop_name = None
    if cropId:
        crop_name = CROP_ID_TO_NAME.get(cropId)

    # Get data from existing dashboard service
    db = next(get_db())
    result = get_dashboard(db, period=period, crop_name=crop_name)

    # Map to frontend KPI format
    kpis = [
        {
            "id": "total_area_ha",
            "labelVi": "Tổng diện tích",
            "value": result["total_area_ha"]["current"],
            "unit": "ha",
            "qoqDeltaPercent": result["total_area_ha"]["change_percent"],
            "yoyDeltaPercent": 0.0,  # Not implemented in current service
        },
        {
            "id": "avg_yield_per_ha",
            "labelVi": "Năng suất trung bình",
            "value": result["avg_yield_per_ha"]["current"],
            "unit": "tấn/ha",
            "qoqDeltaPercent": result["avg_yield_per_ha"]["change_percent"],
            "yoyDeltaPercent": 0.0,
        },
        {
            "id": "disease_case_count",
            "labelVi": "Số ca sâu bệnh",
            "value": result["disease_case_count"]["current"],
            "unit": "ca",
            "qoqDeltaPercent": result["disease_case_count"]["change_percent"],
            "yoyDeltaPercent": 0.0,
        },
        {
            "id": "disease_rate_percent",
            "labelVi": "Tỷ lệ sâu bệnh",
            "value": result["disease_rate_percent"]["current"],
            "unit": "%",
            "qoqDeltaPercent": result["disease_rate_percent"]["change_percent"],
            "yoyDeltaPercent": 0.0,
        },
    ]

    return {
        "period": period,
        "cropId": cropId,
        "kpis": kpis,
        "districtYield": [],  # Would need district data in DB
        "diseaseCases": [],   # Would need aggregated disease data
        "diseaseTrend": [],   # Would need historical disease data
        "districtRankings": [],  # Would need complex queries
    }
