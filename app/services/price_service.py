"""
Module phân tích/dự báo giá thị trường.

GHI CHÚ: Kiến trúc gốc đề xuất Prophet, nhưng Prophet yêu cầu build backend
Stan (C++), thường gây lỗi cài đặt trong môi trường không có sẵn compiler/
mạng bị chặn tải CmdStan. Để đảm bảo chạy được ổn định trong 48h, module này
dùng Holt-Winters Exponential Smoothing (statsmodels) — thuần Python, không
cần compile, vẫn xử lý tốt xu hướng + mùa vụ cho bài toán dự báo giá ngắn hạn.

Nếu môi trường của bạn cài được Prophet (có compiler + mạng không chặn
GitHub release của CmdStan), có thể thay thế hàm `_fit_and_forecast()` bằng
Prophet mà không cần đổi API/response phía trên.
"""
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.config import SAMPLE_PRICE_CSV

_history_cache: dict[str, pd.DataFrame] = {}


def _load_history(crop_name: str) -> pd.DataFrame:
    if crop_name in _history_cache:
        return _history_cache[crop_name]

    df = pd.read_csv(SAMPLE_PRICE_CSV, parse_dates=["date"])
    subset = df[df["crop_name"] == crop_name][["date", "price"]].sort_values("date").reset_index(drop=True)
    _history_cache[crop_name] = subset
    return subset


def _fit_and_forecast(history: pd.DataFrame, periods: int) -> list[float]:
    series = history.set_index("date")["price"]
    series.index = pd.DatetimeIndex(series.index).to_period("D").to_timestamp()

    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add",
        seasonal_periods=90,  # chu kỳ mùa vụ ~ theo quý, khớp với dữ liệu mẫu sinh ra
        initialization_method="estimated",
    )
    fitted = model.fit(optimized=True)
    forecast = fitted.forecast(periods)
    return [max(float(v), 0.0) for v in forecast.values]


def get_market_price(crop_name: str, forecast_days: int = 14) -> dict:
    history = _load_history(crop_name)
    if history.empty:
        raise ValueError(f"Không có dữ liệu giá cho crop_name='{crop_name}'")

    current_price = float(history["price"].iloc[-1])
    recent_avg = float(history["price"].tail(14).mean())
    older_avg = float(history["price"].tail(28).head(14).mean()) if len(history) >= 28 else recent_avg

    if recent_avg > older_avg * 1.02:
        trend = "increasing"
    elif recent_avg < older_avg * 0.98:
        trend = "decreasing"
    else:
        trend = "stable"

    forecast_values = _fit_and_forecast(history, forecast_days)
    last_date = history["date"].iloc[-1]
    forecast_points = [
        {"date": (last_date + pd.Timedelta(days=i + 1)).date(), "price": round(v, 0)}
        for i, v in enumerate(forecast_values)
    ]

    history_points = [
        {"date": row["date"].date(), "price": round(row["price"], 0)}
        for _, row in history.tail(60).iterrows()
    ]

    return {
        "crop_name": crop_name,
        "current_price": round(current_price, 0),
        "trend": trend,
        "history": history_points,
        "forecast": forecast_points,
    }
