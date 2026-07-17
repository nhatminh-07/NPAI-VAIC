from pathlib import Path
from typing import Tuple

from PIL import Image


class CustomDiseaseModel:
    """Mô hình chẩn đoán bệnh nhẹ, deterministic và dễ chạy trong demo."""

    def _extract_color_features(self, image_path: str) -> Tuple[float, float, float, float]:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((220, 220))
        pixels = list(img.getdata())
        total = max(len(pixels), 1)

        green_count = 0
        brown_count = 0
        dark_count = 0
        red_count = 0

        for r, g, b in pixels:
            if g > r and g > b and g > 60:
                green_count += 1
            if r > 100 and g > 60 and b < 90 and r >= g:
                brown_count += 1
            if r < 70 and g < 70 and b < 70:
                dark_count += 1
            if r > 120 and g < 80 and b < 80:
                red_count += 1

        return (
            green_count / total,
            brown_count / total,
            dark_count / total,
            red_count / total,
        )

    def predict(self, image_path: str, crop_name: str) -> Tuple[str, float]:
        crop_name = (crop_name or "rice").strip().lower()
        green_ratio, brown_ratio, dark_ratio, red_ratio = self._extract_color_features(image_path)

        if brown_ratio < 0.06 and green_ratio > 0.45:
            return "healthy", round(min(0.95, 0.88 + green_ratio * 0.08), 2)

        if crop_name == "rice":
            if brown_ratio > 0.18 and red_ratio > 0.09:
                return "rice_blast", round(min(0.96, 0.82 + brown_ratio * 0.8), 2)
            return "bacterial_leaf_blight", round(min(0.95, 0.78 + brown_ratio * 0.7), 2)

        if crop_name == "coffee":
            if dark_ratio > 0.12 and brown_ratio > 0.15:
                return "coffee_berry_borer", round(min(0.96, 0.80 + brown_ratio * 0.9), 2)
            return "coffee_leaf_rust", round(min(0.95, 0.77 + brown_ratio * 0.8), 2)

        if dark_ratio > 0.11 and brown_ratio > 0.12:
            return "vegetable_downy_mildew", round(min(0.95, 0.78 + brown_ratio * 0.7), 2)
        return "vegetable_aphids", round(min(0.94, 0.75 + brown_ratio * 0.6), 2)
