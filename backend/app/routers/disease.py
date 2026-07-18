import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import DiseaseDetection, Farm
from app.schemas import DiseaseDetectionResponse
from app.services.disease_model import get_model
from app.services.disease_rules import get_disease_display

router = APIRouter(prefix="", tags=["Disease Detection"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/detect-disease", response_model=DiseaseDetectionResponse)
async def detect_disease_endpoint(
    image: UploadFile = File(..., description="Ảnh lá/thân cây"),
    crop_name: str = Form("rice", description="rice | coffee | vegetable"),
    farm_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Định dạng ảnh không hỗ trợ: {ext}")

    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)
    content = await image.read()
    with open(save_path, "wb") as f:
        f.write(content)

    model = get_model()
    disease_key, confidence = model.predict(save_path, crop_name=crop_name)
    disease_label_vi, scientific_name, severity, recommendations = get_disease_display(disease_key)
    image_url = f"/static/uploaded_images/{filename}"
    recommendation_text = "; ".join(recommendations)

    # Nếu có farm_id hợp lệ, lấy district từ farm.location; nếu không thì dùng mặc định
    district = "Điện Biên"
    farm = None
    if farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if farm:
            district = farm.location

    record = DiseaseDetection(
        farm_id=farm_id if farm else None,
        district=district,
        crop_type=crop_name,
        image_url=image_url,
        disease_label=disease_label_vi,
        scientific_name=scientific_name,
        confidence=confidence,
        severity=severity,
        recommendation=recommendation_text,
    )
    db.add(record)
    db.commit()

    return DiseaseDetectionResponse(
        disease_label=disease_label_vi,
        confidence=confidence,
        recommendation=recommendation_text,
        image_url=image_url,
    )