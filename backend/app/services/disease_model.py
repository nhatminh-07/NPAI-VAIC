"""Mô hình chẩn đoán bệnh cây trồng dùng MobileNetV2 fine-tune trên PlantVillage
(HuggingFace: linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification).
"""

from functools import lru_cache
from typing import Tuple

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
PLANTVILLAGE_TO_APP_LABEL = {
    "Apple___Apple_scab": "bacterial_leaf_blight",
    "Apple___Black_rot": "coffee_berry_borer",
    "Apple___Cedar_apple_rust": "coffee_leaf_rust",
    "Apple___healthy": "healthy",
    "Blueberry___healthy": "healthy",
    "Cherry_(including_sour)___Powdery_mildew": "vegetable_downy_mildew",
    "Cherry_(including_sour)___healthy": "healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "vegetable_downy_mildew",
    "Corn_(maize)___Common_rust_": "coffee_leaf_rust",
    "Corn_(maize)___Northern_Leaf_Blight": "rice_blast",
    "Corn_(maize)___healthy": "healthy",
    "Grape___Black_rot": "coffee_berry_borer",
    "Grape___Esca_(Black_Measles)": "coffee_berry_borer",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "rice_blast",
    "Grape___healthy": "healthy",
    "Orange___Haunglongbing_(Citrus_greening)": "bacterial_leaf_blight",
    "Peach___Bacterial_spot": "bacterial_leaf_blight",
    "Peach___healthy": "healthy",
    "Pepper,_bell___Bacterial_spot": "bacterial_leaf_blight",
    "Pepper,_bell___healthy": "healthy",
    "Potato___Early_blight": "rice_blast",
    "Potato___Late_blight": "rice_blast",
    "Potato___healthy": "healthy",
    "Raspberry___healthy": "healthy",
    "Soybean___healthy": "healthy",
    "Squash___Powdery_mildew": "vegetable_downy_mildew",
    "Strawberry___Leaf_scorch": "rice_blast",
    "Strawberry___healthy": "healthy",
    "Tomato___Bacterial_spot": "bacterial_leaf_blight",
    "Tomato___Early_blight": "rice_blast",
    "Tomato___Late_blight": "rice_blast",
    "Tomato___Leaf_Mold": "vegetable_downy_mildew",
    "Tomato___Septoria_leaf_spot": "vegetable_downy_mildew",
    "Tomato___Spider_mites Two-spotted_spider_mite": "vegetable_aphids",
    "Tomato___Target_Spot": "vegetable_downy_mildew",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "vegetable_aphids",
    "Tomato___Tomato_mosaic_virus": "vegetable_aphids",
    "Tomato___healthy": "healthy",
}


@lru_cache(maxsize=1)
def _load_model():
    """Load model + processor một lần duy nhất (cache theo process)."""
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
    model.eval()
    return processor, model


class CustomDiseaseModel:
    """Wrapper giữ nguyên interface cũ (predict(image_path, crop_name) -> (label, confidence))
    nhưng suy luận bằng model MobileNetV2 thật thay vì heuristic màu sắc."""

    def __init__(self):
        self.processor, self.model = _load_model()

    def predict(self, image_path: str, crop_name: str) -> Tuple[str, float]:
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")

        with torch.no_grad():
            logits = self.model(**inputs).logits

        probs = torch.softmax(logits, dim=-1)[0]
        top_idx = int(torch.argmax(probs).item())
        confidence = round(float(probs[top_idx].item()), 2)

        raw_label = self.model.config.id2label[top_idx]
        app_label = PLANTVILLAGE_TO_APP_LABEL.get(raw_label, "healthy")

        return app_label, confidence