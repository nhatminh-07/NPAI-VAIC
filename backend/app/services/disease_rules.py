"""Module dùng chung: mapping disease_key -> tên hiển thị / tên khoa học / mức độ / khuyến nghị.
Trước đây 2 router (disease.py và frontend_disease.py) tự định nghĩa các dict này riêng,
dễ bị lệch nhau khi 1 bên sửa mà bên kia quên cập nhật. Giờ dùng chung 1 nguồn duy nhất.
"""

import json
from typing import List, Tuple

from app.config import DISEASE_RULES_JSON

with open(DISEASE_RULES_JSON, "r", encoding="utf-8") as f:
    DISEASE_RULES = json.load(f)

SCIENTIFIC_NAMES = {
    "healthy": "Không có bệnh",
    "rice_blast": "Pyricularia oryzae",
    "bacterial_leaf_blight": "Xanthomonas oryzae pv. oryzae",
    "coffee_leaf_rust": "Hemileia vastatrix",
    "coffee_berry_borer": "Hypothenemus hampei",
    "vegetable_downy_mildew": "Peronosporaceae",
    "vegetable_aphids": "Aphidoidea",
}

SEVERITY_MAP = {
    "healthy": "healthy",
    "rice_blast": "moderate",
    "bacterial_leaf_blight": "severe",
    "coffee_leaf_rust": "mild",
    "coffee_berry_borer": "moderate",
    "vegetable_downy_mildew": "mild",
    "vegetable_aphids": "moderate",
}


def _parse_recommendations(recommendation: str) -> List[str]:
    steps = recommendation.replace(";", ",").split(",")
    return [s.strip() for s in steps if s.strip()]


def get_disease_display(disease_key: str) -> Tuple[str, str, str, List[str]]:
    """Trả về (label_vi, scientific_name, severity, recommendations_list) cho 1 disease_key."""
    rule = DISEASE_RULES.get(disease_key, DISEASE_RULES["healthy"])
    label_vi = rule["label_vi"]
    scientific_name = SCIENTIFIC_NAMES.get(disease_key, "Không xác định")
    severity = SEVERITY_MAP.get(disease_key, "moderate")
    recommendations = _parse_recommendations(rule["recommendation"])
    return label_vi, scientific_name, severity, recommendations