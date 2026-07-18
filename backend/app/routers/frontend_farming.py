"""
Router cho frontend - Quản lý vùng canh tác & vụ canh tác.
Xem bối cảnh đầy đủ tại backend/REQUIREMENTS_farming_management.md và đoạn
"GHI CHÚ CHO BACKEND ENGINEER" phía trên getFarmingRegions() ở frontend/src/lib/api.ts.

Endpoints:
    POST   /farming-regions        - cán bộ tạo 1 vùng canh tác (trang /management)
    GET    /farming-regions        - danh sách vùng canh tác
    DELETE /farming-regions/{id}   - xoá 1 vùng canh tác (kèm vụ canh tác của nó)
    POST   /farming-periods        - nông dân khai 1 vụ canh tác, gắn với 1 vùng có sẵn
    GET    /farming-periods        - danh sách vụ canh tác
    DELETE /farming-periods/{id}   - xoá 1 vụ canh tác

Không cần userId/token - app hiện không có đăng nhập thật, giống cách /disease-report
đang hoạt động.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FarmingRegion, FarmingPeriod, DiseaseDetection
from app.schemas import (
    FarmingRegionCreate,
    FarmingRegionItem,
    FarmingRegionListResponse,
    FarmingPeriodCreate,
    FarmingPeriodItem,
    FarmingPeriodListResponse,
)

router = APIRouter(tags=["Frontend - Farming Management"])

VALID_CROP_TYPES = {"rice", "coffee", "vegetable"}


@router.post("/farming-regions", response_model=FarmingRegionItem)
def create_farming_region(payload: FarmingRegionCreate, db: Session = Depends(get_db)):
    """Cán bộ tạo 1 vùng canh tác mới."""
    if not payload.name.strip():
        raise HTTPException(400, "Tên vùng canh tác không được để trống")

    region = FarmingRegion(name=payload.name.strip(), district=payload.district, area_ha=payload.areaHa)
    db.add(region)
    db.commit()
    db.refresh(region)

    return FarmingRegionItem(
        id=region.id,
        name=region.name,
        district=region.district,
        areaHa=region.area_ha,
        createdAt=region.created_at.isoformat(),
    )


@router.get("/farming-regions", response_model=FarmingRegionListResponse)
def list_farming_regions(db: Session = Depends(get_db)):
    """Danh sách vùng canh tác - dùng cho cả bảng ở trang /management (cán bộ) và
    dropdown chọn vùng ở trang /farming-periods (nông dân), /scan (báo cáo bệnh)."""
    regions = db.query(FarmingRegion).order_by(FarmingRegion.created_at.desc()).all()
    return FarmingRegionListResponse(
        regions=[
            FarmingRegionItem(
                id=r.id,
                name=r.name,
                district=r.district,
                areaHa=r.area_ha,
                createdAt=r.created_at.isoformat(),
            )
            for r in regions
        ]
    )


@router.delete("/farming-regions/{region_id}")
def delete_farming_region(region_id: int, db: Session = Depends(get_db)):
    """Xoá 1 vùng canh tác. Đồng thời xoá các vụ canh tác thuộc vùng đó, và GỠ liên kết
    vùng khỏi các báo cáo sâu bệnh (giữ lại bản ghi báo cáo, chỉ set farming_region_id=NULL)
    để không mất lịch sử chẩn đoán khi cán bộ xoá vùng."""
    region = db.query(FarmingRegion).filter(FarmingRegion.id == region_id).first()
    if not region:
        raise HTTPException(404, "Không tìm thấy vùng canh tác")

    db.query(FarmingPeriod).filter(FarmingPeriod.region_id == region_id).delete(synchronize_session=False)
    db.query(DiseaseDetection).filter(DiseaseDetection.farming_region_id == region_id).update(
        {DiseaseDetection.farming_region_id: None}, synchronize_session=False
    )
    db.delete(region)
    db.commit()
    return {"ok": True}


@router.post("/farming-periods", response_model=FarmingPeriodItem)
def create_farming_period(payload: FarmingPeriodCreate, db: Session = Depends(get_db)):
    """Nông dân khai báo 1 vụ canh tác trong 1 vùng canh tác có sẵn."""
    if payload.cropType not in VALID_CROP_TYPES:
        raise HTTPException(400, f"cropType không hợp lệ: {payload.cropType}")

    region = db.query(FarmingRegion).filter(FarmingRegion.id == payload.regionId).first()
    if not region:
        raise HTTPException(404, "Không tìm thấy vùng canh tác")

    # Diện tích các vụ đã khai trong vùng này cộng thêm vụ mới không được vượt quá
    # diện tích toàn vùng cán bộ đã khoanh định.
    existing_area = (
        db.query(func.coalesce(func.sum(FarmingPeriod.area_ha), 0.0))
        .filter(FarmingPeriod.region_id == payload.regionId)
        .scalar()
        or 0.0
    )
    if existing_area + payload.areaHa > region.area_ha + 1e-9:
        remaining = max(region.area_ha - existing_area, 0.0)
        raise HTTPException(
            400,
            f"Diện tích vượt quá phần còn trống của vùng canh tác "
            f"(còn lại {remaining:.2f} ha / tổng {region.area_ha:.2f} ha)",
        )

    period = FarmingPeriod(
        region_id=payload.regionId,
        crop_type=payload.cropType,
        area_ha=payload.areaHa,
        crop_count=payload.cropCount,
    )
    db.add(period)
    db.commit()
    db.refresh(period)

    return FarmingPeriodItem(
        id=period.id,
        regionId=period.region_id,
        regionName=region.name,
        cropType=period.crop_type,
        areaHa=period.area_ha,
        cropCount=period.crop_count or 0,
        createdAt=period.created_at.isoformat(),
    )


@router.get("/farming-periods", response_model=FarmingPeriodListResponse)
def list_farming_periods(db: Session = Depends(get_db)):
    """Danh sách vụ canh tác đã khai báo, kèm regionName đã join sẵn."""
    periods = (
        db.query(FarmingPeriod, FarmingRegion)
        .join(FarmingRegion, FarmingPeriod.region_id == FarmingRegion.id)
        .order_by(FarmingPeriod.created_at.desc())
        .all()
    )
    return FarmingPeriodListResponse(
        periods=[
            FarmingPeriodItem(
                id=period.id,
                regionId=period.region_id,
                regionName=region.name,
                cropType=period.crop_type,
                areaHa=period.area_ha,
                cropCount=period.crop_count or 0,
                createdAt=period.created_at.isoformat(),
            )
            for period, region in periods
        ]
    )


@router.delete("/farming-periods/{period_id}")
def delete_farming_period(period_id: int, db: Session = Depends(get_db)):
    """Xoá 1 vụ canh tác (planting operation)."""
    period = db.query(FarmingPeriod).filter(FarmingPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Không tìm thấy vụ canh tác")
    db.delete(period)
    db.commit()
    return {"ok": True}
