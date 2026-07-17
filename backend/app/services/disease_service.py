"""Module nhận diện sâu bệnh dùng mô hình riêng nhẹ và ổn định cho demo."""

import json

from app.config import DISEASE_RULES_JSON
from app.services.disease_model import CustomDiseaseModel

with open(DISEASE_RULES_JSON, "r", encoding="utf-8") as f:
    DISEASE_RULES = json.load(f)

_model = CustomDiseaseModel()


def detect_disease(image_path: str, crop_name: str = "rice") -> dict:
    label, confidence = _model.predict(image_path, crop_name)
    rule = DISEASE_RULES.get(label, DISEASE_RULES["healthy"])
    return {
        "disease_label": rule["label_vi"],
        "confidence": confidence,
        "recommendation": rule["recommendation"],
    }
