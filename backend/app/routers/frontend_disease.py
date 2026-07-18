"""
Router cho frontend - API contract theo định dạng Next.js frontend.
Endpoint: POST /disease/detect
Response: DiseaseDetectionResult
"""
import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.config import UPLOAD_DIR
from app.services.disease_model import get_model

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


def _parse_recommendations(disease_key: str) -> List[str]:
    """Generate recommendations based on disease key."""
    base = [
        "Theo dõi tình trạng cây trồng thường xuyên.",
        "Kiểm tra độ ẩm đất và điều chỉnh tưới tiêu.",
        "Tham khảo ý kiến chuyên gia nông nghiệp địa phương.",
    ]
    if disease_key == "healthy":
        return ["Cây trồng khỏe mạnh. Tiếp tục duy trì chăm sóc bình thường."]
    specific = {
        "rice_blast": [
            "Cách ly cây bệnh để tránh lây lan.",
            "Phun thuốc trừ nấm Validacin hoặc Fuji-One.",
            "Giảm bón đạm, tăng bón kali.",
            "Thau nước thường xuyên để hạ nhiệt độ.",
        ],
        "bacterial_leaf_blight": [
            "Cách ly cây bệnh ngay lập tức.",
            "Phun thuốc kháng khuẩn đồng (Copper-based).",
            "Không tưới nước lên lá.",
            "Bón phân cân đối, tránh bón thừa đạm.",
        ],
        "coffee_leaf_rust": [
            "Tỉa cành thông thoáng, tăng ánh sáng.",
            "Phun thuốc gốc đồng hoặc Daconil.",
            "Thu gom lá rụng tiêu hủy.",
            "Bón phân đầy đủ để tăng sức đề kháng.",
        ],
        "coffee_berry_borer": [
            "Thu hoạch sớm quả chín.",
            "Phun thuốc Decamethrin hoặc Cypermethrin.",
            "Vệ sinh vườn sạch sẽ.",
            "Sử dụng bẫy côn trùng.",
        ],
        "vegetable_downy_mildew": [
            "Cách ly cây bệnh.",
            "Phun thuốc Ridomil Gold hoặc Acrobat.",
            "Tăng cường thoáng gió, giảm độ ẩm.",
            "Tránh tưới nước lên lá.",
        ],
        "vegetable_aphids": [
            "Phun nước áp lực cao để rửa trôi rệp.",
            "Sử dụng thuốc trừ sâu sinh học hoặc Confidor.",
            "Trồng cây có mùi hương xua đuổi rệp.",
            "Thu hút thiên địch (bọ rùa, ong ký sinh).",
        ],
    }
    return specific.get(disease_key, base[:])


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

    # Get model prediction
    model = get_model()
    disease_key, confidence = model.predict(save_path, crop_name=cropType)

    # Map disease key to Vietnamese label
    label_names = {
        "healthy": "Cây khỏe mạnh",
        "rice_blast": "Đạo ôn lúa",
        "bacterial_leaf_blight": "Bạc lá vi khuẩn",
        "coffee_leaf_rust": "Gỉ sắt cà phê",
        "coffee_berry_borer": "Sâu đục quả cà phê",
        "vegetable_downy_mildew": "Sương mai rau màu",
        "vegetable_aphids": "Rệp hại rau màu",
    }
    disease_name = label_names.get(disease_key, disease_key)

    return {
        "diseaseName": disease_name,
        "scientificName": _get_scientific_name(disease_key),
        "confidence": confidence,
        "severity": _get_severity(disease_key, confidence),
        "recommendations": _parse_recommendations(disease_key),
        "imageUrl": f"/static/uploaded_images/{filename}",
    }
