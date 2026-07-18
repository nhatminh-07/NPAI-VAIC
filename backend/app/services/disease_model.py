"""
Mô hình chẩn đoán bệnh cây trồng với fallback heuristic.
Hoạt động ổn định trên Windows dù PyTorch/TorchVision không import được.
"""

import json
import os
from typing import Any, Optional, Tuple

from PIL import Image

try:
    import torch
    import torchvision.transforms as T
except Exception:  # pragma: no cover - environment dependent
    torch = None
    T = None

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "mobilenetv3_plant_disease.pth")
LABELS_PATH = os.path.join(MODEL_DIR, "class_labels.json")

MOBILE_TO_APP_LABEL = {
    "0": "bacterial_leaf_blight",
    "1": "coffee_berry_borer",
    "2": "coffee_leaf_rust",
    "3": "healthy",
    "4": "healthy",
    "5": "vegetable_downy_mildew",
    "6": "healthy",
    "7": "vegetable_downy_mildew",
    "8": "coffee_leaf_rust",
    "9": "rice_blast",
    "10": "healthy",
    "11": "coffee_berry_borer",
    "12": "coffee_berry_borer",
    "13": "rice_blast",
    "14": "healthy",
    "15": "bacterial_leaf_blight",
    "16": "bacterial_leaf_blight",
    "17": "healthy",
    "18": "bacterial_leaf_blight",
    "19": "healthy",
    "20": "rice_blast",
    "21": "rice_blast",
    "22": "healthy",
    "23": "healthy",
    "24": "healthy",
    "25": "vegetable_downy_mildew",
    "26": "rice_blast",
    "27": "healthy",
    "28": "bacterial_leaf_blight",
    "29": "rice_blast",
    "30": "rice_blast",
    "31": "vegetable_downy_mildew",
    "32": "vegetable_downy_mildew",
    "33": "vegetable_aphids",
    "34": "vegetable_downy_mildew",
    "35": "vegetable_aphids",
    "36": "vegetable_aphids",
    "37": "healthy",
}


APP_LABEL_NAMES = {
    "healthy": "Cây khỏe mạnh",
    "rice_blast": "Đạo ôn lúa",
    "bacterial_leaf_blight": "Bạc lá vi khuẩn",
    "coffee_leaf_rust": "Gỉ sắt cà phê",
    "coffee_berry_borer": "Sâu đục quả cà phê",
    "vegetable_downy_mildew": "Sương mai rau màu",
    "vegetable_aphids": "Rệp hại rau màu",
}


def _build_mobilenet_model(num_classes: int = 38) -> Optional[Any]:
    """Build MobileNetV3-Small model architecture when torch is available."""
    if torch is None or T is None:
        return None

    try:
        import torchvision.models as models
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"[DiseaseModel] Could not import torchvision.models: {exc}")
        return None

    try:
        return models.mobilenet_v3_small(num_classes=num_classes)
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"[DiseaseModel] Could not build MobileNetV3: {exc}")
        return None


class MobileNetDiseaseModel:
    """Wrapper cho MobileNetV3-Small disease detection model."""

    _instance: Optional["MobileNetDiseaseModel"] = None
    _model: Optional[Any] = None
    _labels: Optional[dict] = None
    _transform: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        """Load labels and model from local files when possible."""
        if os.path.exists(LABELS_PATH):
            with open(LABELS_PATH, "r", encoding="utf-8") as f:
                self._labels = json.load(f)
        else:
            self._labels = {}

        self._model = _build_mobilenet_model(num_classes=38)

        if self._model is None:
            print("[DiseaseModel] torch/torchvision unavailable or model build failed; using heuristic")
            self._transform = None
            return

        if os.path.exists(MODEL_PATH):
            try:
                state_dict = torch.load(MODEL_PATH, map_location="cpu")
                self._model.load_state_dict(state_dict)
                print(f"[DiseaseModel] Loaded MobileNetV3 from {MODEL_PATH}")
            except Exception as exc:
                print(f"[DiseaseModel] Warning: Could not load model weights: {exc}")
                print("[DiseaseModel] Falling back to heuristic model")
                self._model = None
                self._transform = None
                return
        else:
            print(f"[DiseaseModel] Model not found at {MODEL_PATH}, using heuristic")
            self._model = None
            self._transform = None
            return

        self._transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def predict(self, image_path: str, crop_name: str = "rice") -> Tuple[str, float]:
        """Dự đoán bệnh từ ảnh."""
        image = Image.open(image_path).convert("RGB")

        if self._model is None or self._transform is None or torch is None:
            return self._heuristic_predict(image, crop_name)

        img_tensor = self._transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = self._model(img_tensor)
            probs = torch.softmax(outputs, dim=-1)[0]
            confidence, predicted_idx = torch.max(probs, dim=-1)
            predicted_idx = predicted_idx.item()
            confidence = confidence.item()

        raw_label = self._labels.get(str(predicted_idx), f"Class_{predicted_idx}")
        app_label = MOBILE_TO_APP_LABEL.get(str(predicted_idx), "healthy")
        return app_label, round(confidence, 2)

    def _heuristic_predict(self, image: Image.Image, crop_name: str) -> Tuple[str, float]:
        """Fallback heuristic khi không có model."""
        image.thumbnail((220, 220))
        pixels = list(image.getdata())
        total = max(len(pixels), 1)

        green_count = sum(1 for r, g, b in pixels if g > r and g > b and g > 60)
        brown_count = sum(1 for r, g, b in pixels if r > 100 and g > 60 and b < 90 and r >= g)
        dark_count = sum(1 for r, g, b in pixels if r < 70 and g < 70 and b < 70)

        green_ratio = green_count / total
        brown_ratio = brown_count / total
        dark_ratio = dark_count / total

        if brown_ratio < 0.06 and green_ratio > 0.45:
            return "healthy", round(min(0.95, 0.88 + green_ratio * 0.08), 2)

        if crop_name == "rice":
            if brown_ratio > 0.18:
                return "rice_blast", round(min(0.96, 0.82 + brown_ratio * 0.8), 2)
            return "bacterial_leaf_blight", round(min(0.95, 0.78 + brown_ratio * 0.7), 2)

        if crop_name == "coffee":
            if dark_ratio > 0.12 and brown_ratio > 0.15:
                return "coffee_berry_borer", round(min(0.96, 0.80 + brown_ratio * 0.9), 2)
            return "coffee_leaf_rust", round(min(0.95, 0.77 + brown_ratio * 0.8), 2)

        if dark_ratio > 0.11 and brown_ratio > 0.12:
            return "vegetable_downy_mildew", round(min(0.95, 0.78 + brown_ratio * 0.7), 2)
        return "vegetable_aphids", round(min(0.94, 0.75 + brown_ratio * 0.6), 2)


_model_instance: Optional[MobileNetDiseaseModel] = None


def get_model() -> MobileNetDiseaseModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = MobileNetDiseaseModel()
    return _model_instance
