from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DashboardResponse
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard_endpoint(
    period: str = Query("quarter", pattern="^(quarter|year)$"),
    crop_name: Optional[str] = Query(None, description="rice | coffee | vegetable"),
    db: Session = Depends(get_db),
):
    result = get_dashboard(db, period=period, crop_name=crop_name)
    return DashboardResponse(**result)
