from fastapi import APIRouter, HTTPException, Query

from app.schemas import MarketPriceResponse
from app.services.price_service import get_market_price

router = APIRouter(prefix="", tags=["Market Price"])


@router.get("/market-price", response_model=MarketPriceResponse)
def market_price_endpoint(
    crop_name: str = Query(..., description="rice | coffee | vegetable"),
    forecast_days: int = Query(14, ge=1, le=60),
):
    try:
        result = get_market_price(crop_name=crop_name, forecast_days=forecast_days)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Lỗi lấy dữ liệu giá: {e}")

    return MarketPriceResponse(**result)
