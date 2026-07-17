"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: GET /dashboard
Response: DashboardResult
"""
from datetime import date, timedelta
from typing import Optional, List
import re
from collections import defaultdict

from fastapi import APIRouter, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

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
    """Parse period string like '2026-Q3' -> (start, end)."""
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

    # Previous period
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

    db = next(get_db())

    crop_id = None
    if crop_name:
        crop = db.query(Crop).filter(Crop.name == crop_name).first()
        crop_id = crop.id if crop else None

    # === KPIs ===
    def get_total_area(start, end):
        q = db.query(func.coalesce(func.sum(Farm.area), 0.0))
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

    def get_avg_yield(start, end):
        q = db.query(func.coalesce(func.avg(YieldPrediction.predicted_yield), 0.0)).join(Farm).filter(
            YieldPrediction.created_at >= start, YieldPrediction.created_at <= end
        )
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

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

    # === District Yield (group by location) ===
    district_yield_cur = defaultdict(lambda: {"yield": 0.0, "count": 0})
    district_yield_prev = defaultdict(lambda: {"yield": 0.0, "count": 0})

    farms_q = db.query(Farm)
    if crop_id:
        farms_q = farms_q.filter(Farm.crop_id == crop_id)
    farms = farms_q.all()
    farm_by_id = {f.id: f for f in farms}

    yield_preds_cur = db.query(YieldPrediction).filter(
        YieldPrediction.created_at >= current_start,
        YieldPrediction.created_at <= current_end
    ).all()
    yield_preds_prev = db.query(YieldPrediction).filter(
        YieldPrediction.created_at >= prev_start,
        YieldPrediction.created_at <= prev_end
    ).all()

    for pred in yield_preds_cur:
        farm = farm_by_id.get(pred.farm_id)
        if farm:
            loc = farm.location
            district_yield_cur[loc]["yield"] += pred.predicted_yield
            district_yield_cur[loc]["count"] += 1

    for pred in yield_preds_prev:
        farm = farm_by_id.get(pred.farm_id)
        if farm:
            loc = farm.location
            district_yield_prev[loc]["yield"] += pred.predicted_yield
            district_yield_prev[loc]["count"] += 1

    district_yield_data = []
    for loc in set(list(district_yield_cur.keys()) + list(district_yield_prev.keys())):
        cur_avg = (district_yield_cur[loc]["yield"] / district_yield_cur[loc]["count"]) if district_yield_cur[loc]["count"] > 0 else 0
        prev_avg = (district_yield_prev[loc]["yield"] / district_yield_prev[loc]["count"]) if district_yield_prev[loc]["count"] > 0 else 0
        district_yield_data.append({
            "district": loc,
            "currentYieldTPerHa": round(cur_avg, 2),
            "previousYieldTPerHa": round(prev_avg, 2),
        })

    # === Disease Cases (group by disease label) ===
    disease_q = db.query(DiseaseDetection).filter(
        DiseaseDetection.created_at >= current_start,
        DiseaseDetection.created_at <= current_end
    )
    if crop_id:
        disease_q = disease_q.join(Farm).filter(Farm.crop_id == crop_id)
    diseases = disease_q.all()

    disease_count = defaultdict(int)
    for d in diseases:
        disease_count[d.disease_label] += 1

    disease_cases_data = [
        {"diseaseName": name, "cases": count}
        for name, count in sorted(disease_count.items(), key=lambda x: -x[1])
    ]

    # === Disease Trend (last 4 quarters) ===
    disease_trend_data = []
    for i in range(3, -1, -1):
        q_offset = i
        q_year = current_start.year
        q_num = (current_start.month - 1) // 3 + 1 - q_offset
        while q_num <= 0:
            q_num += 4
            q_year -= 1
        q_start_month = (q_num - 1) * 3 + 1
        q_start = date(q_year, q_start_month, 1)
        q_end_month = q_start_month + 2
        q_end_year = q_year
        if q_end_month > 12:
            q_end_month -= 12
            q_end_year += 1
        q_end = date(q_end_year, q_end_month, 28)

        q = db.query(func.count(DiseaseDetection.id)).filter(
            DiseaseDetection.created_at >= q_start,
            DiseaseDetection.created_at <= q_end
        )
        if crop_id:
            q = q.join(Farm).filter(Farm.crop_id == crop_id)
        count = int(q.scalar() or 0)
        disease_trend_data.append({
            "quarterLabel": f"Q{q_num}/{q_year}",
            "cases": count,
        })

    # === District Rankings ===
    district_stats = defaultdict(lambda: {"yield": 0.0, "count": 0, "disease": 0, "area": 0.0})
    for farm in farms:
        district_stats[farm.location]["area"] += farm.area

    for pred in yield_preds_cur:
        farm = farm_by_id.get(pred.farm_id)
        if farm:
            district_stats[farm.location]["yield"] += pred.predicted_yield
            district_stats[farm.location]["count"] += 1

    for d in diseases:
        farm = farm_by_id.get(d.farm_id)
        if farm:
            district_stats[farm.location]["disease"] += 1

    rankings = []
    for loc, stats in district_stats.items():
        if stats["count"] > 0:
            yield_avg = stats["yield"] / stats["count"]
            output_tons = stats["yield"]  # tổng yield
        else:
            yield_avg = 0
            output_tons = 0
        rankings.append({
            "district": loc,
            "yieldTPerHa": round(yield_avg, 2),
            "outputTons": round(output_tons, 2),
            "diseaseCases": stats["disease"],
        })
    rankings.sort(key=lambda x: -x["yieldTPerHa"])
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return {
        "period": period,
        "cropId": cropId,
        "kpis": kpis,
        "districtYield": district_yield_data,
        "diseaseCases": disease_cases_data,
        "diseaseTrend": disease_trend_data,
        "districtRankings": rankings,
    }