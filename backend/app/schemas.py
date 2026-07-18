from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Disease Detection ----------
class DiseaseDetectionResponse(BaseModel):
    disease_label: str
    confidence: float
    recommendation: str
    image_url: str


class DiseaseReportItem(BaseModel):
    id: int
    district: str
    cropType: str
    diseaseName: str
    severity: str
    affectedPlantCount: int
    reportedAt: str  # ISO date string


class DiseaseReportListResponse(BaseModel):
    reports: List[DiseaseReportItem]


# ---------- Yield Forecast ----------
class YieldPredictRequest(BaseModel):
    farm_id: Optional[int] = None
    crop_name: str = Field(..., examples=["rice", "coffee", "vegetable"])
    area_ha: float = Field(..., gt=0, description="Diện tích canh tác (hecta)")
    sowing_date: date
    location: str = Field(default="Điện Biên")
    avg_temperature: Optional[float] = Field(
        default=None, description="Nhiệt độ TB (°C). Nếu bỏ trống sẽ dùng dữ liệu thời tiết mẫu."
    )
    total_rainfall: Optional[float] = Field(
        default=None, description="Tổng lượng mưa vụ (mm). Nếu bỏ trống sẽ dùng dữ liệu mẫu."
    )
    prev_season_yield: Optional[float] = Field(
        default=None, description="Năng suất vụ trước (tấn/ha), nếu có"
    )


class YieldPredictResponse(BaseModel):
    predicted_yield_tons: float
    predicted_yield_per_ha: float
    harvest_date: date
    season: str
    notes: str


# ---------- Market Price ----------
class PricePoint(BaseModel):
    date: date
    price: float


class MarketPriceResponse(BaseModel):
    crop_name: str
    current_price: float
    unit: str = "VND/kg"
    trend: str  # "increasing" | "decreasing" | "stable"
    history: List[PricePoint]
    forecast: List[PricePoint]


# ---------- Dashboard ----------
class PeriodMetric(BaseModel):
    label: str
    current: float
    previous: float
    change_percent: float


class DashboardResponse(BaseModel):
    period: str
    crop_name: Optional[str]
    total_area_ha: PeriodMetric
    avg_yield_per_ha: PeriodMetric
    disease_case_count: PeriodMetric
    disease_rate_percent: PeriodMetric
    year_over_year_note: str