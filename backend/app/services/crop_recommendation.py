"""
Crop Recommendation Service - Dựa trên thông số đất và khí hậu.
Model: RandomForestClassifier từ AI-Crop-Advisor
Dữ liệu cây trồng: crop_info.json
"""

import json
import os
from typing import Tuple, Optional

import joblib
import numpy as np

from app.config import BASE_DIR

# Đường dẫn model
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "crop_recommendation")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_recommendation_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")

# Đường dẫn crop info JSON
CROP_INFO_PATH = os.path.join(BASE_DIR, "app", "data", "crop_info.json")

# Cache crop info
_crop_info_cache = None


def _load_crop_info() -> dict:
    """Load crop info từ JSON file."""
    global _crop_info_cache
    if _crop_info_cache is not None:
        return _crop_info_cache

    try:
        with open(CROP_INFO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Build a flat dict: key = crop name (rice, coffee, vegetable, ...)
            # với thông tin cơ bản nhất
            _crop_info_cache = {}
            for crop in data.get("crops", []):
                name = crop["name"]
                name_vi = crop.get("name_vi", name)
                # Lấy variety đầu tiên
                varieties = crop.get("varieties", [])
                if varieties:
                    var = varieties[0]
                    seasons = var.get("seasons", [])
                    if seasons:
                        first_season = seasons[0]
                        # Build season string
                        season_str = ", ".join([s.get("season", "") for s in seasons])
                        # Calculate duration range
                        min_days = first_season.get("growth_days_min", 0)
                        max_days = first_season.get("growth_days_max", 0)
                        duration = f"{min_days}-{max_days} ngày" if min_days or max_days else "Tùy mùa"
                        # Yield range
                        min_yield = first_season.get("yield_ton_ha_min", 0)
                        max_yield = first_season.get("yield_ton_ha_max", 0)
                        yield_str = f"{min_yield}-{max_yield} tấn/ha" if min_yield or max_yield else "Tùy điều kiện"
                        # Tips từ ideal_weather
                        weather = first_season.get("ideal_weather", {})
                        temp = weather.get("temp_c_min") and weather.get("temp_c_max")
                        temp_str = f"Nhiệt: {weather.get('temp_c_min', '?')}-{weather.get('temp_c_max', '?')}°C" if temp else ""
                        tips = temp_str if temp_str else "Tham khảo thêm"
                    else:
                        season_str = "Liên hệ"
                        duration = "Liên hệ"
                        yield_str = "Liên hệ"
                        tips = "Cần tư vấn thêm"
                else:
                    season_str = "Liên hệ"
                    duration = "Liên hệ"
                    yield_str = "Liên hệ"
                    tips = "Cần tư vấn thêm"

                _crop_info_cache[name] = {
                    "name_vi": name_vi,
                    "season": season_str,
                    "duration": duration,
                    "yield": yield_str,
                    "tips": tips,
                }

            return _crop_info_cache
    except Exception as e:
        print(f"[CropRecommender] Error loading crop_info.json: {e}")
        # Fallback to empty dict
        return {}


# Load crop info at module level
CROP_INFO = _load_crop_info()


class CropRecommender:
    """Wrapper cho RandomForest crop recommendation model."""

    _instance: Optional['CropRecommender'] = None
    _model = None
    _encoder = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        """Load model từ file."""
        if os.path.exists(MODEL_PATH):
            try:
                self._model = joblib.load(MODEL_PATH)
                print(f"[CropRecommender] Loaded model from {MODEL_PATH}")
            except Exception as e:
                print(f"[CropRecommender] Error loading model: {e}")
                self._model = None
        else:
            print(f"[CropRecommender] Model not found at {MODEL_PATH}")
            self._model = None

        if os.path.exists(ENCODER_PATH):
            try:
                self._encoder = joblib.load(ENCODER_PATH)
                print(f"[CropRecommender] Loaded encoder from {ENCODER_PATH}")
            except Exception as e:
                print(f"[CropRecommender] Error loading encoder: {e}")
                self._encoder = None
        else:
            self._encoder = None

    def recommend(
        self,
        N: float,
        P: float,
        K: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
    ) -> dict:
        """
        Đề xuất cây trồng dựa trên thông số đất và khí hậu.

        Args:
            N: Nitrogen (0-140)
            P: Phosphorus (5-145)
            K: Potassium (5-205)
            temperature: Nhiệt độ (°C)
            humidity: Độ ẩm (%)
            ph: Độ pH đất (0-14)
            rainfall: Lượng mưa (mm)

        Returns:
            dict với crop được đề xuất và thông tin chi tiết
        """
        # Clamp values to valid ranges
        N = max(0, min(140, N))
        P = max(5, min(145, P))
        K = max(5, min(205, K))
        temperature = max(0, min(50, temperature))
        humidity = max(0, min(100, humidity))
        ph = max(0, min(14, ph))
        rainfall = max(0, min(300, rainfall))

        if self._model is not None and self._encoder is not None:
            # Dùng model
            features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
            prediction = self._model.predict(features)[0]
            crop_name = self._encoder.inverse_transform([prediction])[0]
        else:
            # Fallback: simple heuristic
            crop_name = self._simple_recommend(N, P, K, temperature, ph, rainfall)

        # Get crop info
        crop_key = crop_name.lower().replace(" ", "").replace("_", "")
        crop_info = CROP_INFO.get(crop_key, {
            "name_vi": crop_name,
            "season": "Liên hệ chuyên gia",
            "duration": "Xem hướng dẫn",
            "yield": "Tùy điều kiện",
            "tips": "Cần tư vấn thêm",
        })

        return {
            "recommended_crop": crop_name,
            "crop_name_vi": crop_info["name_vi"],
            "season": crop_info["season"],
            "duration": crop_info["duration"],
            "expected_yield": crop_info["yield"],
            "tips": crop_info["tips"],
            "confidence": 0.85,
        }

    def _simple_recommend(self, N: float, P: float, K: float, temperature: float, ph: float, rainfall: float) -> str:
        """Simple heuristic recommendation fallback."""
        # Very basic logic based on conditions
        if ph < 5.5:
            return "rice" if rainfall > 100 else "mungbean"
        elif ph > 7.0:
            return "coffee" if temperature < 30 else "pomegranate"
        elif temperature > 25 and humidity > 60:
            return "mango" if rainfall > 150 else "watermelon"
        else:
            return "maize"


# Singleton
_recommender: Optional[CropRecommender] = None


def get_recommender() -> CropRecommender:
    global _recommender
    if _recommender is None:
        _recommender = CropRecommender()
    return _recommender
