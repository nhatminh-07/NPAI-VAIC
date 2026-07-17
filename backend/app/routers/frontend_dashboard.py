"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: GET /dashboard
Response: DashboardResult
"""
from datetime import date, timedelta
from typing import Optional, List
import re

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Farm, YieldPrediction, DiseaseDetection, Crop

router = APIRouter(prefix="", tags=["Frontend - Dashboard"])

# Map frontend crop ID to backend crop name
CROP_ID_TO_NAME = {
    1: "rice",
    2: "coffee",
    3: "vegetable",
}


def parse_period(period: str) -> tuple[date, date]:
    """
    Parse period string like '2026-Q3' or 'quarter'/'year'.
    Returns (start_date, end_date) for the period.
    """
    # Match pattern like "2026-Q3"
    match = re.match(r'(\d{4})-Q(\d)', period)
    if match:
        year, quarter = int(match.group(1)), int(match.group(2))
        start_month = (quarter - 1) * 3 + 1
        start = date(year, start_month, 1)
        end_month = start_month + 2
        end_year = year
        if end_month > 12:
            end_month -= 12
            end_year += 1
        end = date(end_year, end_month, 28)
        return start, end

    # Fallback: use current quarter
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    year = today.year
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end_year = year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    end = date(end_year, end_month, 28)
    return start, end


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 1)


@router.get("/dashboard")
async def get_dashboard_frontend(
    period: str = Query("quarter", description="2026-Q3, quarter, or year"),
    cropId: Optional[int] = Query(None, description="1=rice, 2=coffee, 3=vegetable"),
):
    """Frontend API: Dashboard so sánh kỳ."""
    crop_name = None
    if cropId:
        crop_name = CROP_ID_TO_NAME.get(cropId)

    # Parse period
    current_start, current_end = parse_period(period)

    # Calculate previous period (previous quarter)
    quarter = (current_start.month - 1) // 3 + 1
    year = current_start.year
    quarter -= 1
    prev_year = year
    if quarter <= 0:
        quarter = 4
        prev_year -= 1
    prev_start_month = (quarter - 1) * 3 + 1
    prev_start = date(prev_year, prev_start_month, 1)
    prev_end_month = prev_start_month + 2
    prev_end_year = prev_year
    if prev_end_month > 12:
        prev_end_month -= 12
        prev_end_year += 1
    prev_end = date(prev_end_year, prev_end_month, 28)

    # Query database
    db = next(get_db())

    crop_id = None
    if crop_name:
        crop = db.query(Crop).filter(Crop.name == crop_name).first()
        crop_id = crop.id if crop else None

    # Total area
    def get_total_area(start, end):
        q = db.query(func.coalesce(func.sum(Farm.area), 0.0))
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

    # Average yield
    def get_avg_yield(start, end):
        q = db.query(func.coalesce(func.avg(YieldPrediction.predicted_yield), 0.0)).join(Farm).filter(
            YieldPrediction.created_at >= start, YieldPrediction.created_at <= end
        )
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

    # Disease count
    def get_disease_count(start, end):
        q = db.query(func.count(DiseaseDetection.id)).join(Farm).filter(
            DiseaseDetection.created_at >= start, DiseaseDetection.created_at <= end
        )
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return int(q.scalar() or 0)

    cur_area = get_total_area(current_start, current_end)
    prev_area = get_total_area(prev_start, prev_end)

    cur_yield = get_avg_yield(current_start, current_end)
    prev_yield = get_avg_yield(prev_start, prev_end)

    cur_disease = get_disease_count(current_start, current_end)
    prev_disease = get_disease_count(prev_start, prev_end)

    total_farms = max(db.query(func.count(Farm.id)).scalar() or 1, 1)
    cur_rate = cur_disease / total_farms * 100
    prev_rate = prev_disease / total_farms * 100

    kpis = [
        {
            "id": "total_area_ha",
            "labelVi": "Tổng diện tích",
            "value": round(cur_area, 2),
            "unit": "ha",
            "qoqDeltaPercent": _pct_change(cur_area, prev_area),
            "yoyDeltaPercent": 0.0,
        },
        {
            "id": "avg_yield_per_ha",
            "labelVi": "Năng suất trung bình",
            "value": round(cur_yield, 2),
            "unit": "tấn/ha",
            "qoqDeltaPercent": _pct_change(cur_yield, prev_yield),
            "yoyDeltaPercent": 0.0,
        },
        {
            "id": "disease_case_count",
            "labelVi": "Số ca sâu bệnh",
            "value": cur_disease,
            "unit": "ca",
            "qoqDeltaPercent": _pct_change(float(cur_disease), float(prev_disease)),
            "yoyDeltaPercent": 0.0,
        },
        {
            "id": "disease_rate_percent",
            "labelVi": "Tỷ lệ sâu bệnh",
            "value": round(cur_rate, 1),
            "unit": "%",
            "qoqDeltaPercent": _pct_change(cur_rate, prev_rate),
            "yoyDeltaPercent": 0.0,
        },
    ]

    return {
        "period": period,
        "cropId": cropId,
        "kpis": kpis,
        "districtYield": [],
        "diseaseCases": [],
        "diseaseTrend": [],
        "districtRankings": [],
    }
