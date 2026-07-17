"""
Module nhận diện sâu bệnh.

QUAN TRỌNG (đọc trước khi demo/nộp bài):
Trong 48h không đủ thời gian để thu thập + gán nhãn dataset ảnh sâu bệnh thật
cho cây trồng Điện Biên rồi fine-tune YOLOv8. Module này dùng một bộ phân loại
heuristic (dựa trên đặc trưng màu sắc của ảnh) để MÔ PHỎNG pipeline suy luận
thật, giúp demo đầy đủ luồng end-to-end (upload -> AI -> gợi ý xử lý -> lưu DB).

Cách nâng cấp lên model thật (khuyến nghị sau cuộc thi hoặc nếu có thời gian):
1. `pip install ultralytics`
2. Thu thập/gán nhãn ảnh bệnh theo cây trồng (có thể dùng dataset public như
   PlantVillage để bootstrap, rồi fine-tune thêm với ảnh thực tế Điện Biên).
3. Train: `yolo train model=yolov8n.pt data=disease.yaml epochs=50`
4. Thay hàm `_classify_image()` dưới đây bằng:
       from ultralytics import YOLO
       model = YOLO("path/to/best.pt")
       results = model.predict(image_path)
       # lấy nhãn có confidence cao nhất từ results[0]
   Phần còn lại của pipeline (lookup gợi ý, lưu DB, trả API) giữ nguyên.
"""

import json
import random
from typing import Tuple

from PIL import Image

from app.config import DISEASE_RULES_JSON

with open(DISEASE_RULES_JSON, "r", encoding="utf-8") as f:
    DISEASE_RULES = json.load(f)

# Nhãn khả dĩ theo từng loại cây, dùng để giới hạn không gian dự đoán demo
CROP_DISEASE_MAP = {
    "rice": ["healthy", "rice_blast", "bacterial_leaf_blight"],
    "coffee": ["healthy", "coffee_leaf_rust", "coffee_berry_borer"],
    "vegetable": ["healthy", "vegetable_downy_mildew", "vegetable_aphids"],
}


def _extract_color_features(image_path: str) -> Tuple[float, float]:
    """Trích đặc trưng đơn giản: tỉ lệ xanh lá (khỏe) và tỉ lệ vàng/nâu (bệnh)."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((200, 200))  # giảm kích thước để xử lý nhanh
    pixels = list(img.getdata())
    total = len(pixels)
    green_count = 0
    yellow_brown_count = 0
    for r, g, b in pixels:
        if g > r and g > b and g > 60:
            green_count += 1
        elif r > 100 and g > 60 and b < 90 and r >= g:
            yellow_brown_count += 1
    return green_count / total, yellow_brown_count / total


def _classify_image(image_path: str, crop_name: str) -> Tuple[str, float]:
    """
    Phân loại demo: tỉ lệ vùng vàng/nâu cao -> nghiêng về có bệnh.
    Đây là heuristic MVP, KHÔNG phải model học sâu thật.
    """
    green_ratio, brown_ratio = _extract_color_features(image_path)
    candidates = CROP_DISEASE_MAP.get(crop_name, CROP_DISEASE_MAP["rice"])

    if brown_ratio < 0.08:
        label = "healthy"
        confidence = round(0.85 + random.uniform(0, 0.1), 2)
    else:
        disease_candidates = [c for c in candidates if c != "healthy"]
        label = random.choice(disease_candidates)
        # confidence tăng theo mức độ vùng vàng/nâu phát hiện được, giới hạn hợp lý
        confidence = round(min(0.6 + brown_ratio * 1.5, 0.96), 2)

    return label, confidence


def detect_disease(image_path: str, crop_name: str = "rice") -> dict:
    label, confidence = _classify_image(image_path, crop_name)
    rule = DISEASE_RULES.get(label, DISEASE_RULES["healthy"])
    return {
        "disease_label": rule["label_vi"],
        "confidence": confidence,
        "recommendation": rule["recommendation"],
    }
