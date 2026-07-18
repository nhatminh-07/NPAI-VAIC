"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: GET /dashboard
Response: DashboardResult

THIẾT KẾ (đã hợp nhất + theo kỳ - xem backend/REQUIREMENTS_farming_management.md):
    Dashboard lấy dữ liệu HOÀN TOÀN từ hệ thống Quản lý (vùng canh tác → vụ canh tác →
    báo cáo sâu bệnh gắn vùng), KHÔNG dùng bảng Farm/YieldPrediction cũ.

    MỌI SỐ LIỆU ĐỀU ĐƯỢC LỌC THEO KỲ (quý) ĐANG CHỌN - mỗi kỳ có dữ liệu RIÊNG:
    - Vùng canh tác / vụ canh tác / báo cáo bệnh "thuộc" 1 kỳ dựa trên created_at.
    - Tổng diện tích (kỳ X) = SUM diện tích các VÙNG được tạo trong kỳ X.
    - Vì vậy quý hiện tại (demo: Quý 3/2026) BẮT ĐẦU TRỐNG (seed chỉ tạo dữ liệu cho các
      quý trước); khi cán bộ tạo vùng / nông dân khai vụ canh tác / báo cáo bệnh trong lúc
      demo, dữ liệu đó có created_at = bây giờ = Quý hiện tại nên hiện lên NGAY.
    - Nhóm theo huyện dùng FarmingRegion.district (chuẩn frontend/src/constants/districts.ts).
"""
from datetime import date, datetime
from typing import Optional
import re
import calendar
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farm, DiseaseDetection, Crop, FarmingRegion, FarmingPeriod

router = APIRouter(prefix="", tags=["Frontend - Dashboard"])

CROP_ID_TO_NAME = {1: "rice", 2: "coffee", 3: "vegetable"}

# Năng suất cơ sở (tấn/ha) theo loại cây - dùng chung với seed_data.py.
BASE_YIELD = {"rice": 5.5, "coffee": 2.5, "vegetable": 12.0}

# Mật độ cây/ha tham chiếu (theo dữ liệu seed). Năng suất thực tế của 1 vụ = năng suất
# cơ sở điều chỉnh theo mật độ trồng thật (crop_count / area_ha) mà nông dân nhập - trồng
# dày hơn thì năng suất/ha cao hơn, thưa hơn thì thấp hơn (giới hạn 0.6x..1.4x để hợp lý).
REF_DENSITY = 200.0


def _period_yield_per_ha(p) -> float:
    """Năng suất/ha thực tế của 1 vụ canh tác, dựa trên mật độ trồng nông dân khai."""
    base = BASE_YIELD.get(p.crop_type, 0.0)
    if not p.crop_count or p.area_ha <= 0:
        return base
    factor = min(1.4, max(0.6, (p.crop_count / p.area_ha) / REF_DENSITY))
    return base * factor


def _quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end_year = year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    last_day = calendar.monthrange(end_year, end_month)[1]
    end = date(end_year, end_month, last_day)
    return start, end


def parse_period(period: str) -> tuple[date, date]:
    """Parse 'YYYY-Qn' -> (start, end). Fallback: quý hiện tại theo ngày hệ thống."""
    match = re.match(r"(\d{4})-Q(\d)", period)
    if match:
        return _quarter_bounds(int(match.group(1)), int(match.group(2)))
    today = date.today()
    return _quarter_bounds(today.year, (today.month - 1) // 3 + 1)


def _prev_quarter_bounds(current_start: date) -> tuple[date, date]:
    quarter = (current_start.month - 1) // 3 + 1 - 1
    year = current_start.year
    if quarter <= 0:
        quarter = 4
        year -= 1
    return _quarter_bounds(year, quarter)


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 1)


def _in_range(dt, start: date, end: date) -> bool:
    if dt is None:
        return False
    d = dt.date() if isinstance(dt, datetime) else dt
    return start <= d <= end


@router.get("/dashboard")
async def get_dashboard_frontend(
    period: str = Query("quarter", description="vd '2026-Q3', hoặc 'quarter'"),
    cropId: Optional[int] = Query(None, description="1=rice, 2=coffee, 3=vegetable"),
    db: Session = Depends(get_db),
):
    """Frontend API: Dashboard so sánh kỳ - mọi số liệu lọc theo kỳ đang chọn."""
    crop_name = CROP_ID_TO_NAME.get(cropId) if cropId else None

    current_start, current_end = parse_period(period)
    prev_start, prev_end = _prev_quarter_bounds(current_start)

    # --- Tải toàn bộ, rồi CẮT THEO KỲ (created_at) ---
    all_regions = db.query(FarmingRegion).all()
    region_by_id = {r.id: r for r in all_regions}
    regions_cur = [r for r in all_regions if _in_range(r.created_at, current_start, current_end)]
    regions_prev = [r for r in all_regions if _in_range(r.created_at, prev_start, prev_end)]

    all_periods = db.query(FarmingPeriod).all()
    if crop_name:
        all_periods = [p for p in all_periods if p.crop_type == crop_name]
    periods_cur = [p for p in all_periods if _in_range(p.created_at, current_start, current_end)]
    periods_prev = [p for p in all_periods if _in_range(p.created_at, prev_start, prev_end)]

    all_diseases = db.query(DiseaseDetection).all()
    if crop_name:
        all_diseases = [d for d in all_diseases if d.crop_type == crop_name]
    diseases_cur = [d for d in all_diseases if _in_range(d.created_at, current_start, current_end)]
    diseases_prev = [d for d in all_diseases if _in_range(d.created_at, prev_start, prev_end)]

    # ===== KPI 1: Tổng diện tích =====
    if crop_name:
        # Lọc cây trồng: tổng diện tích các vụ canh tác của cây đó trong kỳ.
        cur_area = sum(p.area_ha for p in periods_cur)
        prev_area = sum(p.area_ha for p in periods_prev)
    else:
        # Không lọc: tổng diện tích tất cả VÙNG canh tác được tạo trong kỳ.
        cur_area = sum(r.area_ha for r in regions_cur)
        prev_area = sum(r.area_ha for r in regions_prev)

    # Fallback an toàn: chưa có vùng nào trong TOÀN BỘ hệ thống (DB trống trước khi seed)
    # -> dùng SUM(Farm.area) để dashboard không hoàn toàn trống. KHÔNG áp dụng cho trường
    # hợp "kỳ này trống nhưng kỳ khác có dữ liệu" (đó là hành vi mong muốn của demo).
    if not all_regions:
        farms_q = db.query(Farm)
        if crop_name:
            crop = db.query(Crop).filter(Crop.name == crop_name).first()
            if crop:
                farms_q = farms_q.filter(Farm.crop_id == crop.id)
        cur_area = float(sum(f.area for f in farms_q.all()))
        prev_area = cur_area

    # ===== KPI 2: Năng suất trung bình (tấn/ha, trọng số diện tích) =====
    def area_weighted_yield(period_list) -> float:
        area = sum(p.area_ha for p in period_list)
        if area <= 0:
            return 0.0
        return sum(p.area_ha * _period_yield_per_ha(p) for p in period_list) / area

    cur_yield = area_weighted_yield(periods_cur)
    prev_yield = area_weighted_yield(periods_prev)

    # ===== KPI 3: Số ca sâu bệnh =====
    cur_disease = len(diseases_cur)
    prev_disease = len(diseases_prev)

    # ===== KPI 4: Tỷ lệ sâu bệnh (theo diện tích vùng canh tác TRONG KỲ) =====
    def disease_rate(regions_in_term, diseases_in_term) -> float:
        denom = sum(r.area_ha for r in regions_in_term)
        if denom <= 0:
            return 0.0
        term_region_ids = {r.id for r in regions_in_term}
        affected_ids = {
            d.farming_region_id for d in diseases_in_term
            if d.farming_region_id in term_region_ids
        }
        affected_area = sum(region_by_id[rid].area_ha for rid in affected_ids)
        return affected_area / denom * 100

    cur_rate = disease_rate(regions_cur, diseases_cur)
    prev_rate = disease_rate(regions_prev, diseases_prev)

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

    # ===== Năng suất theo huyện (kỳ hiện tại vs kỳ trước) =====
    def district_yield_map(period_list):
        acc = defaultdict(lambda: {"area": 0.0, "yield_area": 0.0})
        for p in period_list:
            r = region_by_id.get(p.region_id)
            if not r:
                continue
            acc[r.district]["area"] += p.area_ha
            acc[r.district]["yield_area"] += p.area_ha * _period_yield_per_ha(p)
        return acc

    dy_cur = district_yield_map(periods_cur)
    dy_prev = district_yield_map(periods_prev)

    district_yield_data = []
    for dist in sorted(set(dy_cur) | set(dy_prev)):
        cur_avg = dy_cur[dist]["yield_area"] / dy_cur[dist]["area"] if dy_cur[dist]["area"] > 0 else 0.0
        prev_avg = dy_prev[dist]["yield_area"] / dy_prev[dist]["area"] if dy_prev[dist]["area"] > 0 else 0.0
        district_yield_data.append({
            "district": dist,
            "currentYieldTPerHa": round(cur_avg, 2),
            "previousYieldTPerHa": round(prev_avg, 2),
        })

    # ===== Số ca bệnh theo loại (kỳ hiện tại) =====
    disease_count = defaultdict(int)
    for d in diseases_cur:
        disease_count[d.disease_label] += 1
    disease_cases_data = [
        {"diseaseName": name, "cases": count}
        for name, count in sorted(disease_count.items(), key=lambda x: -x[1])
    ]

    # ===== Xu hướng dịch bệnh (4 quý gần nhất) =====
    disease_trend_data = []
    cur_q = (current_start.month - 1) // 3 + 1
    cur_y = current_start.year
    for i in range(3, -1, -1):
        q_num = cur_q - i
        q_year = cur_y
        while q_num <= 0:
            q_num += 4
            q_year -= 1
        q_start, q_end = _quarter_bounds(q_year, q_num)
        count = sum(1 for d in all_diseases if _in_range(d.created_at, q_start, q_end))
        disease_trend_data.append({"quarterLabel": f"Q{q_num}/{q_year}", "cases": count})

    # ===== Xếp hạng huyện (chỉ các huyện có vùng canh tác trong kỳ hiện tại) =====
    district_disease = defaultdict(int)
    for d in diseases_cur:
        r = region_by_id.get(d.farming_region_id)
        if r:
            district_disease[r.district] += 1

    cur_districts = sorted({r.district for r in regions_cur})
    rankings = []
    for dist in cur_districts:
        area = dy_cur[dist]["area"]
        yield_area = dy_cur[dist]["yield_area"]
        yield_avg = yield_area / area if area > 0 else 0.0
        rankings.append({
            "district": dist,
            "yieldTPerHa": round(yield_avg, 2),
            "outputTons": round(yield_area, 2),
            "diseaseCases": district_disease[dist],
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
