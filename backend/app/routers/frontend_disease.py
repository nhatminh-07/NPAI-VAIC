"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /disease/detect
Response: DiseaseDetectionResult
"""
import json
import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, DISEASE_RULES_JSON
from app.database import get_db
from app.models import DiseaseReport
from app.schemas import DiseaseReportItem, DiseaseReportListResponse
from app.services.disease_service import detect_disease

router = APIRouter(prefix="/disease", tags=["Frontend - Disease Detection"])

# GET /disease-report KHÔNG nằm dưới prefix /disease (đúng theo contract của frontend),
# nên phải dùng router riêng không prefix, include song song ở main.py.
report_router = APIRouter(tags=["Frontend - Disease Detection"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VALID_CROP_TYPES = {"rice", "coffee", "vegetable"}


def _get_scientific_name(disease_key: str) -> str:
    """Map disease key to scientific name."""
    scientific_names = {
        "healthy": "Không có bệnh",
        "rice_blast": "Pyricularia oryzae",
        "bacterial_leaf_blight": "Xanthomonas oryzae pv. oryzae",
        "coffee_leaf_rust": "Hemileia vastatrix",
        "coffee_berry_borer": "Hypothenemus hampei",
        "vegetable_downy_mildew": "Peronosporaceae",
        "vegetable_aphids": "Aphidoidea",
    }
    return scientific_names.get(disease_key, "Không xác định")


def _get_severity(disease_key: str, confidence: float) -> str:
    """Map disease to severity level."""
    if disease_key == "healthy":
        return "healthy"
    severity_map = {
        "rice_blast": "moderate",
        "bacterial_leaf_blight": "severe",
        "coffee_leaf_rust": "mild",
        "coffee_berry_borer": "moderate",
        "vegetable_downy_mildew": "mild",
        "vegetable_aphids": "moderate",
    }
    return severity_map.get(disease_key, "moderate")


def _parse_recommendations(recommendation: str) -> List[str]:
    """Parse recommendation string into list of steps."""
    # Split by common Vietnamese separators
    steps = recommendation.replace(";", ",").split(",")
    return [s.strip() for s in steps if s.strip()]


@router.post("/detect")
async def detect_disease_frontend(
    image: UploadFile = File(..., description="Ảnh lá/thân cây"),
    cropType: str = Form("rice", description="rice | coffee | vegetable"),
    affectedPlantCount: str = Form(..., description="Số lượng cây bị ảnh hưởng, vd '5'"),
    district: str = Form("Điện Biên", description="Huyện/khu vực báo cáo (tùy chọn)"),
    db: Session = Depends(get_db),
):
    """Frontend API: Nhận diện sâu bệnh + lưu báo cáo vào DB."""
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

    # Save image
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    content = await image.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Call existing service
    result = detect_disease(save_path, crop_name=cropType)

    # Map to frontend response format
    disease_key = result["disease_label"].lower().replace(" ", "_").replace("(", "").replace(")", "")
    if "khỏe" in disease_key or "healthy" in disease_key.lower():
        disease_key = "healthy"

    scientific_name = _get_scientific_name(disease_key)
    severity = _get_severity(disease_key, result["confidence"])
    recommendations = _parse_recommendations(result["recommendation"])
    image_url = f"/static/uploaded_images/{filename}"

    # Lưu báo cáo vào DB để dashboard GET /disease-report đọc lại
    record = DiseaseReport(
        district=district,
        crop_type=cropType,
        disease_name=result["disease_label"],
        scientific_name=scientific_name,
        confidence=result["confidence"],
        severity=severity,
        affected_plant_count=plant_count,
        recommendations=json.dumps(recommendations, ensure_ascii=False),
        image_url=image_url,
    )
    db.add(record)
    db.commit()

    return {
        "diseaseName": result["disease_label"],
        "scientificName": scientific_name,
        "confidence": result["confidence"],
        "severity": severity,
        "recommendations": recommendations,
        "imageUrl": image_url,
    }


@report_router.get("/disease-report", response_model=DiseaseReportListResponse)
@report_router.get("/disease-reports", response_model=DiseaseReportListResponse, include_in_schema=False)
def get_disease_reports(db: Session = Depends(get_db)):
    """Frontend API: GET /disease-report - dashboard tab officer đọc danh sách báo cáo.
    Đăng ký thêm alias /disease-reports (số nhiều) phòng trường hợp frontend gọi nhầm
    tên - cùng trỏ về 1 handler để tránh lệch dữ liệu giữa 2 route.
    """
    rows = db.query(DiseaseReport).order_by(DiseaseReport.reported_at.desc()).all()
    reports = [
        DiseaseReportItem(
            id=row.id,
            district=row.district,
            cropType=row.crop_type,
            diseaseName=row.disease_name,
            severity=row.severity,
            affectedPlantCount=row.affected_plant_count,
            reportedAt=row.reported_at.isoformat(),
        )
        for row in rows
    ]
    return DiseaseReportListResponse(reports=reports)