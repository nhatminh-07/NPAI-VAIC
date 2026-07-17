"""
Train model LightGBM dự báo năng suất/ha từ dữ liệu mẫu.

Chạy: python -m app.ml.train_yield_model
"""
import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from app.config import SAMPLE_YIELD_CSV, YIELD_MODEL_PATH

FEATURE_COLS = ["crop_code", "area_ha", "avg_temperature", "total_rainfall", "prev_season_yield"]
CROP_CODE_MAP = {"rice": 0, "coffee": 1, "vegetable": 2}


def main():
    df = pd.read_csv(SAMPLE_YIELD_CSV)
    df["crop_code"] = df["crop_name"].map(CROP_CODE_MAP)

    X = df[FEATURE_COLS]
    y = df["yield_per_ha"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=15,
        random_state=42,
        verbosity=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"MAE trên tập test (tấn/ha): {mae:.3f}")

    joblib.dump({"model": model, "crop_code_map": CROP_CODE_MAP, "feature_cols": FEATURE_COLS}, YIELD_MODEL_PATH)
    print(f"Đã lưu model -> {YIELD_MODEL_PATH}")


if __name__ == "__main__":
    main()
