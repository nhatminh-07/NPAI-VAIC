"""Router cho tính năng crop recommendation - giao diện frontend."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.crop_recommendation import get_recommender
from app.services.weather_service import get_current_weather, get_forecast_7d

router = APIRouter(prefix="", tags=["frontend"])


class CropRecommendRequest(BaseModel):
    N: float = Field(..., ge=0, le=140, description="Nitrogen (mg/kg)")
    P: float = Field(..., ge=5, le=145, description="Phosphorus (mg/kg)")
    K: float = Field(..., ge=5, le=205, description="Potassium (mg/kg)")
    temperature: float = Field(..., ge=0, le=50, description="Nhiệt độ (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Độ ẩm (%)")
    ph: float = Field(..., ge=0, le=14, description="Độ pH đất")
    rainfall: float = Field(..., ge=0, le=300, description="Lượng mưa (mm/tháng)")


class WeatherRequest(BaseModel):
    lat: float = Field(default=21.8, ge=-90, le=90)
    lon: float = Field(default=103.0, ge=-180, le=180)


@router.post("/crop/recommend")
async def recommend_crop(body: CropRecommendRequest) -> dict:
    """Đề xuất cây trồng dựa trên thông số đất và khí hậu."""
    recommender = get_recommender()
    result = recommender.recommend(
        N=body.N,
        P=body.P,
        K=body.K,
        temperature=body.temperature,
        humidity=body.humidity,
        ph=body.ph,
        rainfall=body.rainfall,
    )
    return {"success": True, "data": result}


@router.get("/weather/current")
async def current_weather(lat: float = 21.8, lon: float = 103.0) -> dict:
    """Lấy thời tiết hiện tại. Mặc định: Điện Biên."""
    weather = get_current_weather(lat=lat, lon=lon)
    return {"success": True, "data": weather}


@router.get("/weather/forecast")
async def weather_forecast(lat: float = 21.8, lon: float = 103.0) -> dict:
    """Lấy dự báo thời tiết 7 ngày."""
    forecast = get_forecast_7d(lat=lat, lon=lon)
    return {"success": True, "data": forecast}
