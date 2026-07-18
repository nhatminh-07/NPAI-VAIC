"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: GET /market/price
Response: MarketPriceResult
"""
from fastapi import APIRouter, Query, HTTPException

from app.services.price_service import get_market_price

router = APIRouter(prefix="/market", tags=["Frontend - Market Price"])

# Map frontend crop ID to backend crop name
CROP_ID_MAP = {
    1: "rice",
    2: "coffee",
    3: "vegetable",
}

CROP_NAMES = {
    1: "Gạo Điện Biên",
    2: "Cà phê Mường Ảng",
    3: "Rau màu vụ đông",
}


@router.get("/price")
async def get_market_price_frontend(
    cropId: int = Query(..., description="1=rice, 2=coffee, 3=vegetable"),
    forecastDays: int = Query(14, ge=1, le=60, description="Số ngày dự báo"),
):
    """Frontend API: Lấy giá thị trường."""
    crop_name = CROP_ID_MAP.get(cropId)
    if not crop_name:
        raise HTTPException(400, "cropId không hợp lệ. Dùng: 1=rice, 2=coffee, 3=vegetable")

    try:
        result = get_market_price(crop_name=crop_name, forecast_days=forecastDays)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Lỗi lấy dữ liệu giá: {e}")

    trend_labels = {
        "increasing": "Xu hướng tăng",
        "decreasing": "Xu hướng giảm",
        "stable": "Ổn định",
    }

    return {
        "cropId": cropId,
        "cropName": CROP_NAMES.get(cropId, crop_name),
        "unit": "VND/kg",
        "history": [
            {"date": p["date"], "price": p["price"]}
            for p in result["history"]
        ],
        "forecast": [
            {"date": p["date"], "price": p["price"], "lowerBand": p["price"] * 0.90, "upperBand": p["price"] * 1.10}
            for p in result["forecast"]
        ],
        "currentPrice": result["current_price"],
        "change7dPercent": result["change_pct"],
        "changeDays": result["change_days"],
        "trendLabel": trend_labels.get(result["trend"], "Không xác định"),
    }
