"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /disease/detect
Response: DiseaseDetectionResult
"""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import DiseaseDetection, FarmingRegion
from app.schemas import DiseaseReportItem, DiseaseReportListResponse
from app.services.disease_model import get_model
from app.services.disease_rules import get_disease_display

router = APIRouter(prefix="/disease", tags=["Frontend - Disease Detection"])

# GET /disease-report KHÔNG nằm dưới prefix /disease (đúng theo contract của frontend),
# nên phải dùng router riêng không prefix, include song song ở main.py.
report_router = APIRouter(tags=["Frontend - Disease Detection"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VALID_CROP_TYPES = {"rice", "coffee", "vegetable"}


@router.post("/detect")
async def detect_disease_frontend(
    image: UploadFile = File(..., description="Ảnh lá/thân cây"),
    cropType: str = Form("rice", description="rice | coffee | vegetable"),
    affectedPlantCount: str = Form(..., description="Số lượng cây bị ảnh hưởng, vd '5'"),
    district: str = Form("Điện Biên", description="Huyện/khu vực báo cáo (tùy chọn)"),
    regionId: Optional[str] = Form(None, description="ID vùng canh tác (tùy chọn), xem FarmingRegion"),
    db: Session = Depends(get_db),
):
    """Frontend API: Nhận diện sâu bệnh + lưu báo cáo vào bảng disease_detections (hợp nhất)."""
    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Định dạng ảnh không hỗ trợ: {ext}")

    if cropType not in VALID_CROP_TYPES:
        raise HTTPException(400, f"cropType không hợp lệ: {cropType}")

    try:
        plant_count = int(affectedPlantCount)
    except (TypeError, ValueError):
        raise HTTPException(400, "affectedPlantCount phải là số nguyên dạng chuỗi, vd '5'")
    if plant_count <= 0:
        raise HTTPException(400, "affectedPlantCount phải lớn hơn 0")

    # regionId tuỳ chọn - nếu farmer chưa chọn vùng canh tác (chưa có vùng nào, hoặc bỏ
    # qua) thì để None, KHÔNG chặn luồng chẩn đoán chính vì đây không phải field bắt buộc.
    region_id: Optional[int] = None
    if regionId:
        try:
            region_id = int(regionId)
        except ValueError:
            raise HTTPException(400, "regionId phải là số nguyên dạng chuỗi, vd '3'")
        if not db.query(FarmingRegion).filter(FarmingRegion.id == region_id).first():
            raise HTTPException(404, "Không tìm thấy vùng canh tác")

    # Save image
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    content = await image.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Gọi model thật (MobileNetV2DiseaseModel.predict trả về (disease_key, confidence))
    model = get_model()
    disease_key, confidence = model.predict(save_path, crop_name=cropType)
    disease_name_vi, scientific_name, severity, recommendations = get_disease_display(disease_key)
    image_url = f"/static/uploaded_images/{filename}"

    # Lưu vào bảng disease_detections hợp nhất (farm_id=None vì báo cáo officer không gắn farm cụ thể)
    record = DiseaseDetection(
        farm_id=None,
        district=district,
        crop_type=cropType,
        image_url=image_url,
        disease_label=disease_name_vi,
        scientific_name=scientific_name,
        confidence=confidence,
        severity=severity,
        affected_plant_count=plant_count,
        recommendation="; ".join(recommendations),
        farming_region_id=region_id,
    )
    db.add(record)
    db.commit()

    return {
        "diseaseName": disease_name_vi,
        "scientificName": scientific_name,
        "confidence": confidence,
        "severity": severity,
        "recommendations": recommendations,
        "imageUrl": image_url,
    }


@report_router.get("/disease-report", response_model=DiseaseReportListResponse)
@report_router.get("/disease-reports", response_model=DiseaseReportListResponse, include_in_schema=False)
def get_disease_reports(db: Session = Depends(get_db)):
    """Frontend API: GET /disease-report - dashboard tab officer đọc danh sách báo cáo,
    đọc từ bảng disease_detections hợp nhất (bao gồm cả báo cáo tạo qua /detect-disease cũ).
    """
    rows = db.query(DiseaseDetection).order_by(DiseaseDetection.created_at.desc()).all()
    reports = [
        DiseaseReportItem(
            id=row.id,
            district=row.district,
            cropType=row.crop_type,
            diseaseName=row.disease_label,
            severity=row.severity or "moderate",
            affectedPlantCount=row.affected_plant_count or 0,
            reportedAt=row.created_at.isoformat(),
        )
        for row in rows
    ]
    return DiseaseReportListResponse(reports=reports)