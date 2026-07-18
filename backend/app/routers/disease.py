import os
import uuid

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import DiseaseDetection, Farm
from app.schemas import DiseaseDetectionResponse
from app.services.disease_model import get_model

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
    disease_label, confidence = model.predict(save_path, crop_name=crop_name)
    image_url = f"/static/uploaded_images/{filename}"

    # Map sang response format
    label_names = {
        "healthy": "Cây khỏe mạnh",
        "rice_blast": "Đạo ôn lúa",
        "bacterial_leaf_blight": "Bạc lá vi khuẩn",
        "coffee_leaf_rust": "Gỉ sắt cà phê",
        "coffee_berry_borer": "Sâu đục quả cà phê",
        "vegetable_downy_mildew": "Sương mai rau màu",
        "vegetable_aphids": "Rệp hại rau màu",
    }
    disease_label_vi = label_names.get(disease_label, disease_label)
    recommendations = [
        "Theo dõi tình trạng cây trồng thường xuyên.",
        "Kiểm tra độ ẩm đất và điều chỉnh tưới tiêu.",
        "Tham khảo ý kiến chuyên gia nông nghiệp địa phương.",
    ]
    if disease_label != "healthy":
        recommendations.insert(0, "Cách ly cây bệnh để tránh lây lan.")
        recommendations.insert(1, "Phun thuốc trừ sâu phù hợp theo hướng dẫn.")

    if farm_id is not None:
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if farm:
            record = DiseaseDetection(
                farm_id=farm_id,
                image_url=image_url,
                disease_label=disease_label_vi,
                confidence=confidence,
                recommendation="; ".join(recommendations),
            )
            db.add(record)
            db.commit()

    return DiseaseDetectionResponse(
        disease_label=disease_label_vi,
        confidence=confidence,
        recommendation="; ".join(recommendations),
        image_url=image_url,
    )
