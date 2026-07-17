from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farm, YieldPrediction
from app.schemas import YieldPredictRequest, YieldPredictResponse
from app.services.yield_service import predict_yield

router = APIRouter(prefix="", tags=["Yield Forecast"])


@router.post("/predict-yield", response_model=YieldPredictResponse)
def predict_yield_endpoint(payload: YieldPredictRequest, db: Session = Depends(get_db)):
    try:
        result = predict_yield(
            crop_name=payload.crop_name,
            area_ha=payload.area_ha,
            sowing_date=payload.sowing_date,
            avg_temperature=payload.avg_temperature,
            total_rainfall=payload.total_rainfall,
            prev_season_yield=payload.prev_season_yield,
        )
    except Exception as e:
        raise HTTPException(500, f"Lỗi dự báo năng suất: {e}")

    if payload.farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
        if farm:
            record = YieldPrediction(
                farm_id=payload.farm_id,
                season=result["season"],
                predicted_yield=result["predicted_yield_tons"],
                harvest_date=result["harvest_date"],
            )
            db.add(record)
            db.commit()

    return YieldPredictResponse(**result)
