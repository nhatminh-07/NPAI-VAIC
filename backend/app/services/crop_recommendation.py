"""
Crop Recommendation Service - Dựa trên thông số đất và khí hậu.
Model: RandomForestClassifier từ AI-Crop-Advisor
"""

import os
from typing import Tuple, Optional

import joblib
import numpy as np

# Đường dẫn model
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "crop_recommendation")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_recommendation_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")

# Thông tin cây trồng (crop information)
CROP_INFO = {
    "rice": {
        "name_vi": "Lúa",
        "season": "Chiêm xuân (Feb-May), Mùa (Jun-Oct)",
        "duration": "110-120 ngày",
        "yield": "4-6 tấn/ha",
        "tips": "Cần nhiều nước, đất phù sa. Bón NPK cân đối.",
    },
    "maize": {
        "name_vi": "Ngô",
        "season": "Vụ xuân (Mar-Jul), Vụ thu (Aug-Nov)",
        "duration": "90-120 ngày",
        "yield": "8-12 tấn/ha",
        "tips": "Cần ánh sáng tốt, thoát nước tốt.",
    },
    "chickpea": {
        "name_vi": "Đậu gà",
        "season": "Vụ đông (Nov-Mar)",
        "duration": "90-120 ngày",
        "yield": "1.5-2.5 tấn/ha",
        "tips": "Chịu hạn tốt, cần đất thoáng.",
    },
    "kidneybeans": {
        "name_vi": "Đậu đỏ",
        "season": "Vụ xuân, vụ thu",
        "duration": "70-90 ngày",
        "yield": "1-2 tấn/ha",
        "tips": "Cần đất tơi xốp, thoát nước.",
    },
    "mungbean": {
        "name_vi": "Đậu xanh",
        "season": "Vụ hè (May-Aug)",
        "duration": "60-70 ngày",
        "yield": "1-1.5 tấn/ha",
        "tips": "Chịu nhiệt tốt, thu hoạch nhanh.",
    },
    "blackgram": {
        "name_vi": "Đậu đen",
        "season": "Vụ hè thu",
        "duration": "75-90 ngày",
        "yield": "1-1.8 tấn/ha",
        "tips": "Cần ấm, cày đất sâu.",
    },
    "lentil": {
        "name_vi": "Đậu lăng",
        "season": "Vụ đông (Nov-Mar)",
        "duration": "90-110 ngày",
        "yield": "1-1.5 tấn/ha",
        "tips": "Chịu lạnh, cần đất phù sa.",
    },
    "pomegranate": {
        "name_vi": "Lựu",
        "season": "Quanh năm",
        "duration": "180-200 ngày (trái)",
        "yield": "15-25 tấn/ha",
        "tips": "Chịu hạn tốt, cần nhiều ánh sáng.",
    },
    "banana": {
        "name_vi": "Chuối",
        "season": "Quanh năm",
        "duration": "9-12 tháng",
        "yield": "25-40 tấn/ha",
        "tips": "Cần nhiều nước, đất giàu dinh dưỡng.",
    },
    "mango": {
        "name_vi": "Xoài",
        "season": "Tết (Apr-Jun)",
        "duration": "3-5 năm (trưởng thành)",
        "yield": "10-20 tấn/ha",
        "tips": "Cần khí hậu nhiệt đới, chịu hạn.",
    },
    "grapes": {
        "name_vi": "Nho",
        "season": "Dec-Mar (thu hoạch)",
        "duration": "180-240 ngày",
        "yield": "15-25 tấn/ha",
        "tips": "Cần giàn, cắt tỉa định kỳ.",
    },
    "watermelon": {
        "name_vi": "Dưa hấu",
        "season": "Vụ xuân, vụ hè",
        "duration": "70-90 ngày",
        "yield": "20-30 tấn/ha",
        "tips": "Cần nhiều nắng, tưới đều.",
    },
    "muskmelon": {
        "name_vi": "Dưa lưới",
        "season": "Vụ xuân",
        "duration": "75-90 ngày",
        "yield": "15-20 tấn/ha",
        "tips": "Cần đất thoáng, không ngập nước.",
    },
    "apple": {
        "name_vi": "Táo",
        "season": "Sep-Nov (thu hoạch)",
        "duration": "3-5 năm (trưởng thành)",
        "yield": "15-30 tấn/ha",
        "tips": "Cần lạnh để ra hoa, đất thoát nước.",
    },
    "orange": {
        "name_vi": "Cam",
        "season": "Nov-Mar (thu hoạch)",
        "duration": "3-4 năm (trưởng thành)",
        "yield": "20-30 tấn/ha",
        "tips": "Cần đất sâu, tưới đều.",
    },
    "papaya": {
        "name_vi": "Đu đủ",
        "season": "Quanh năm",
        "duration": "9-11 tháng",
        "yield": "30-60 tấn/ha",
        "tips": "Sinh trưởng nhanh, cần nhiều phân.",
    },
    "pomegranate": {
        "name_vi": "Lựu",
        "season": "Sep-Dec",
        "duration": "180-200 ngày",
        "yield": "15-25 tấn/ha",
        "tips": "Chịu hạn, cần nắng nhiều.",
    },
    "coffee": {
        "name_vi": "Cà phê",
        "season": "Oct-Dec (thu hoạch)",
        "duration": "2-3 năm (trưởng thành)",
        "yield": "2-4 tấn/ha",
        "tips": "Cần bóng râm nhẹ, đất acid nhẹ.",
    },
}


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
