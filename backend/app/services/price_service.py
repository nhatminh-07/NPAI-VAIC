"""
Module phân tích/dự báo giá thị trường.
Dùng dataset gia_thi_truong_2026.csv

Dùng Holt-Winters Exponential Smoothing (statsmodels) cho dự báo.
"""

import pandas as pd
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.config import BASE_DIR

# Đường dẫn dataset
PRICE_DATA_PATH = f"{BASE_DIR}/app/data/gia_thi_truong_2026.csv"

# Cache
_history_cache = {}


def _load_price_data() -> pd.DataFrame:
    """Load và parse dataset giá thị trường."""
    df = pd.read_csv(PRICE_DATA_PATH)

    # Rename columns
    df = df.rename(columns={
        "Ngay": "date",
        "Nhom_hang": "category",
        "Mat_hang": "product",
        "Gia_thap": "price_low",
        "Gia_cao": "price_high",
        "Don_vi": "unit",
    })

    # Parse date
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")

    # Calculate average price
    df["price"] = df[["price_low", "price_high"]].mean(axis=1)

    # Map category to crop type
    def map_crop_type(row):
        cat = str(row.get("category", "")).lower()
        prod = str(row.get("product", "")).lower()

        if "gạo" in cat or "gao" in prod:
            return "rice"
        elif "lúa" in cat or "lua" in prod:
            return "rice"
        elif "cà phê" in cat or "ca phe" in prod:
            return "coffee"
        elif "rau" in cat or "rau" in prod:
            return "vegetable"
        else:
            return None

    df["crop_type"] = df.apply(map_crop_type, axis=1)

    # Filter valid rows
    df = df[df["crop_type"].notna() & df["price"].notna()]

    return df[["date", "crop_type", "product", "price", "unit"]].sort_values("date")


def _load_history(crop_name: str) -> pd.DataFrame:
    """Load lịch sử giá cho crop."""
    global _history_cache

    if crop_name in _history_cache:
        return _history_cache[crop_name]

    df = _load_price_data()
    subset = df[df["crop_type"] == crop_name][["date", "price"]].copy()
    subset = subset.sort_values("date").reset_index(drop=True)

    _history_cache[crop_name] = subset
    return subset


def _fit_and_forecast(history: pd.DataFrame, periods: int) -> list:
    """Dự báo giá bằng Holt-Winters."""
    if len(history) < 5:
        # Not enough data, return flat forecast
        last_price = history["price"].iloc[-1] if len(history) > 0 else 5000
        return [last_price] * periods

    series = history.set_index("date")["price"]
    series.index = pd.DatetimeIndex(series.index).to_period("D").to_timestamp()

    try:
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=30,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(periods)
        return [max(float(v), 0.0) for v in forecast.values]
    except Exception:
        # Fallback: flat forecast
        last_price = float(history["price"].iloc[-1])
        return [last_price] * periods


def get_market_price(crop_name: str, forecast_days: int = 14) -> dict:
    """
    Lấy giá thị trường và dự báo.

    Args:
        crop_name: rice | coffee | vegetable
        forecast_days: Số ngày dự báo

    Returns:
        dict với current_price, trend, history, forecast
    """
    # Map frontend crop type to dataset
    crop_map = {"rice": "rice", "coffee": "coffee", "vegetable": "vegetable"}
    crop_key = crop_map.get(crop_name, "rice")

    history = _load_history(crop_key)
    if history.empty:
        raise ValueError(f"Không có dữ liệu giá cho '{crop_name}'")

    current_price = float(history["price"].iloc[-1])

    # Calculate trend
    recent = history["price"].tail(7)
    older = history["price"].tail(14).head(7)

    if len(recent) >= 3 and len(older) >= 3:
        recent_avg = recent.mean()
        older_avg = older.mean()

        if recent_avg > older_avg * 1.02:
            trend = "increasing"
        elif recent_avg < older_avg * 0.98:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Forecast
    forecast_values = _fit_and_forecast(history, forecast_days)

    last_date = history["date"].iloc[-1]
    forecast_points = [
        {
            "date": (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "price": round(v, 0)
        }
        for i, v in enumerate(forecast_values)
    ]

    history_points = [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "price": round(row["price"], 0)
        }
        for _, row in history.tail(60).iterrows()
    ]

    # Map crop name for display
    crop_display = {"rice": "Gạo/Lúa", "coffee": "Cà phê", "vegetable": "Rau màu"}

    return {
        "crop_name": crop_display.get(crop_name, crop_name),
        "current_price": round(current_price, 0),
        "trend": trend,
        "history": history_points,
        "forecast": forecast_points,
        "unit": "đ/kg",
    }


def get_available_crops() -> list:
    """Lấy danh sách các loại cây có trong dataset."""
    df = _load_price_data()
    crops = df["crop_type"].unique().tolist()
    return [{"id": i+1, "name": c, "name_vi": c.capitalize()} for i, c in enumerate(crops)]
