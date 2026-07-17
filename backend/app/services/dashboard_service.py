from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Farm, YieldPrediction, DiseaseDetection, Crop


def _period_bounds(period: str, offset: int = 0):
    """Trả về (start, end) của kỳ hiện tại (offset=0) hoặc kỳ trước/cùng kỳ năm trước."""
    today = date.today()
    if period == "quarter":
        quarter = (today.month - 1) // 3 + 1
        quarter -= offset
        year = today.year
        while quarter <= 0:
            quarter += 4
            year -= 1
        start_month = (quarter - 1) * 3 + 1
        start = date(year, start_month, 1)
        end_month = start_month + 2
        end_year = year
        if end_month > 12:
            end_month -= 12
            end_year += 1
        # ngày cuối tháng end_month (xấp xỉ demo: dùng ngày 28 an toàn cho mọi tháng)
        end = date(end_year, end_month, 28)
        return start, end
    else:  # year
        year = today.year - offset
        return date(year, 1, 1), date(year, 12, 31)


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, 1)


def _metric_block(label: str, current: float, previous: float) -> dict:
    return {
        "label": label,
        "current": round(current, 2),
        "previous": round(previous, 2),
        "change_percent": _pct_change(current, previous),
    }


def get_dashboard(db: Session, period: str = "quarter", crop_name: Optional[str] = None) -> dict:
    current_start, current_end = _period_bounds(period, offset=0)
    previous_start, previous_end = _period_bounds(period, offset=1)

    crop_id = None
    if crop_name:
        crop = db.query(Crop).filter(Crop.name == crop_name).first()
        crop_id = crop.id if crop else None

    def area_sum(start, end):
        q = db.query(func.coalesce(func.sum(Farm.area), 0.0))
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

    def avg_yield(start, end):
        q = db.query(func.coalesce(func.avg(YieldPrediction.predicted_yield), 0.0)).join(Farm).filter(
            YieldPrediction.created_at >= start, YieldPrediction.created_at <= end
        )
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return float(q.scalar() or 0.0)

    def disease_count(start, end):
        q = db.query(func.count(DiseaseDetection.id)).join(Farm).filter(
            DiseaseDetection.created_at >= start, DiseaseDetection.created_at <= end
        )
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return int(q.scalar() or 0)

    def farm_count():
        q = db.query(func.count(Farm.id))
        if crop_id:
            q = q.filter(Farm.crop_id == crop_id)
        return int(q.scalar() or 0)

    cur_area = area_sum(current_start, current_end)
    prev_area = area_sum(previous_start, previous_end)

    cur_yield = avg_yield(current_start, current_end)
    prev_yield = avg_yield(previous_start, previous_end)

    cur_disease = disease_count(current_start, current_end)
    prev_disease = disease_count(previous_start, previous_end)

    total_farms = max(farm_count(), 1)
    cur_rate = cur_disease / total_farms * 100
    prev_rate = prev_disease / total_farms * 100

    return {
        "period": period,
        "crop_name": crop_name,
        "total_area_ha": _metric_block("Tổng diện tích (ha)", cur_area, prev_area),
        "avg_yield_per_ha": _metric_block("Năng suất TB (tấn/ha)", cur_yield, prev_yield),
        "disease_case_count": _metric_block("Số ca sâu bệnh phát hiện", cur_disease, prev_disease),
        "disease_rate_percent": _metric_block("Tỷ lệ sâu bệnh (%)", cur_rate, prev_rate),
        "year_over_year_note": (
            "So sánh kỳ trước liền kề. Để so cùng kỳ năm trước, gọi lại API với "
            "tham số period=year hoặc mở rộng offset trong dashboard_service.py."
        ),
    }
