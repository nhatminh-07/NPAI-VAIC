"""
Module phân tích/dự báo giá thị trường.

Luồng dữ liệu:
1. Ưu tiên đọc từ bảng MarketPrice trong DB (đã seed bằng seed_market_prices.py)
2. Fallback sang gia_thi_truong_2026.csv nếu DB trống

Dự báo: Holt-Winters Exponential Smoothing (statsmodels).
"""

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.config import BASE_DIR

PRICE_DATA_PATH = f"{BASE_DIR}/app/data/gia_thi_truong_2026.csv"
_history_cache = {}


def _load_from_db(crop_name: str) -> pd.DataFrame | None:
    """Đọc lịch sử giá từ bảng MarketPrice trong DB. Trả về None nếu DB trống."""
    try:
        from app.database import SessionLocal
        from app.models import MarketPrice, Crop

        db = SessionLocal()
        try:
            crop = db.query(Crop).filter(Crop.name == crop_name).first()
            if not crop:
                return None

            rows = (
                db.query(MarketPrice)
                .filter(MarketPrice.crop_id == crop.id)
                .order_by(MarketPrice.date.asc())
                .all()
            )

            if not rows:
                return None

            return pd.DataFrame([
                {"date": r.date, "price": r.price}
                for r in rows
            ])
        finally:
            db.close()
    except Exception:
        return None


def _load_from_csv(crop_name: str) -> pd.DataFrame:
    """
    Load và parse dataset CSV (gia_thi_truong_2026.csv).
    Dataset wide format: mỗi cột là 1 loại cây.
    """
    df = pd.read_csv(PRICE_DATA_PATH)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

    crop_col_map = {
        "bac_thom_7_price_vnd_kg": "rice",
        "coffee_price_vnd_kg": "coffee",
        "tomato_price_vnd_kg": "vegetable",
    }

    rows = []
    for col, crop_type in crop_col_map.items():
        if col in df.columns:
            temp = df[["date", col]].copy()
            temp.columns = ["date", "price"]
            temp["crop_type"] = crop_type
            rows.append(temp)

    result = pd.concat(rows, ignore_index=True)
    result = result.dropna(subset=["date", "price"])
    return result[result["crop_type"] == crop_name][["date", "price"]].sort_values("date").reset_index(drop=True)


def _load_history(crop_name: str) -> pd.DataFrame:
    """Load lịch sử giá: ưu tiên DB, fallback CSV."""
    global _history_cache

    if crop_name in _history_cache:
        return _history_cache[crop_name]

    # 1. Thử đọc từ DB
    df_db = _load_from_db(crop_name)

    # 2. Fallback CSV
    if df_db is None or df_db.empty:
        print(f"[PriceService] DB trống cho '{crop_name}', fallback sang CSV")
        subset = _load_from_csv(crop_name)
    else:
        subset = df_db.copy().reset_index(drop=True)

    _history_cache[crop_name] = subset
    return subset


def _fit_and_forecast(history: pd.DataFrame, periods: int) -> list:
    """Dự báo giá bằng Holt-Winters với tham số phù hợp cho dữ liệu thưa."""
    if len(history) < 5:
        last_price = history["price"].iloc[-1] if len(history) > 0 else 5000
        return [last_price] * periods

    series = history.set_index("date")["price"]
    series.index = pd.DatetimeIndex(series.index).to_period("D").to_timestamp()

    try:
        model = ExponentialSmoothing(
            series,
            trend="add",
            damped_trend=True,
            seasonal=None,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        forecast = fitted.forecast(periods)
        return [max(float(v), 0.0) for v in forecast.values]
    except Exception:
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
    history = _load_history(crop_name)
    if history.empty:
        raise ValueError(f"Không có dữ liệu giá cho '{crop_name}'")

    current_price = float(history["price"].iloc[-1])
    last_date = pd.Timestamp(history["date"].iloc[-1])

    # Tìm giá cách đây ~7 ngày bằng ngày thực tế
    target_date = last_date - pd.Timedelta(days=7)
    window_start = target_date - pd.Timedelta(days=3)

    older_mask = (history["date"] >= window_start) & (history["date"] < last_date)
    recent_mask = history["date"] >= last_date - pd.Timedelta(days=3)

    recent_window = history.loc[recent_mask, "price"]
    older_window = history.loc[older_mask, "price"]

    if not older_window.empty:
        oldest_in_window = history.loc[older_mask, "date"].min()
        change_days = int((last_date - oldest_in_window).days)
    else:
        change_days = 7

    if len(recent_window) >= 1 and len(older_window) >= 1:
        recent_avg = recent_window.mean()
        older_avg = older_window.mean()

        if recent_avg > older_avg * 1.02:
            trend = "increasing"
        elif recent_avg < older_avg * 0.98:
            trend = "decreasing"
        else:
            trend = "stable"
        change_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg else 0.0
    else:
        trend = "stable"
        change_pct = 0.0

    forecast_values = _fit_and_forecast(history, forecast_days)

    forecast_points = [
        {
            "date": (last_date + pd.Timedelta(days=i + 1)).strftime("%Y-%m-%d"),
            "price": round(v, 0)
        }
        for i, v in enumerate(forecast_values)
    ]

    history_points = [
        {"date": row["date"].strftime("%Y-%m-%d"), "price": round(row["price"], 0)}
        for _, row in history.tail(60).iterrows()
    ]

    crop_display = {"rice": "Lúa Bắc Thơm 7", "coffee": "Cà phê", "vegetable": "Cà chua"}

    return {
        "crop_name": crop_display.get(crop_name, crop_name),
        "current_price": round(current_price, 0),
        "trend": trend,
        "history": history_points,
        "forecast": forecast_points,
        "unit": "đ/kg",
        "change_pct": round(change_pct, 1),
        "change_days": change_days,
    }


def get_available_crops() -> list:
    """Lấy danh sách các loại cây có trong dataset."""
    df = _load_from_csv("rice")
    crops = df["crop_type"].unique().tolist() if not df.empty else ["rice", "coffee", "vegetable"]
    return [{"id": i + 1, "name": c, "name_vi": c.capitalize()} for i, c in enumerate(crops)]
