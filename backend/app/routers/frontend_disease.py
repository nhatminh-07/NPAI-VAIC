"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /disease/detect
Response: DiseaseDetectionResult
"""
import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.config import UPLOAD_DIR, DISEASE_RULES_JSON
from app.services.disease_service import detect_disease

router = APIRouter(prefix="/disease", tags=["Frontend - Disease Detection"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


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
):
    """Frontend API: Nhận diện sâu bệnh."""
    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Định dạng ảnh không hỗ trợ: {ext}")

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

    return {
        "diseaseName": result["disease_label"],
        "scientificName": _get_scientific_name(disease_key),
        "confidence": result["confidence"],
        "severity": _get_severity(disease_key, result["confidence"]),
        "recommendations": _parse_recommendations(result["recommendation"]),
        "imageUrl": f"/static/uploaded_images/{filename}",
    }
