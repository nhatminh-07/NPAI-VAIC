"""
Sinh dữ liệu MẪU (synthetic) để train model dự báo năng suất và demo giá
thị trường, dùng khi chưa có dữ liệu thật từ tỉnh Điện Biên.

Chạy: python -m app.ml.generate_sample_data
"""
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.config import SAMPLE_YIELD_CSV, SAMPLE_PRICE_CSV, DATA_DIR

random.seed(42)
np.random.seed(42)

CROPS = ["rice", "coffee", "vegetable"]

# Năng suất trung bình tham khảo (tấn/ha) mỗi loại cây - số liệu giả định để demo
BASE_YIELD = {"rice": 5.5, "coffee": 2.2, "vegetable": 12.0}
BASE_PRICE = {"rice": 8500, "coffee": 68000, "vegetable": 6000}  # VND/kg


def generate_yield_history(n_rows: int = 600) -> pd.DataFrame:
    rows = []
    for _ in range(n_rows):
        crop = random.choice(CROPS)
        area = round(random.uniform(0.3, 5.0), 2)
        avg_temp = round(random.uniform(18, 28), 1)
        rainfall = round(random.uniform(600, 2200), 0)
        prev_yield = round(BASE_YIELD[crop] * random.uniform(0.7, 1.1), 2)

        # Công thức giả lập quan hệ phi tuyến giữa yếu tố đầu vào và năng suất/ha
        temp_factor = 1 - abs(avg_temp - 23) * 0.02
        rain_factor = 1 - abs(rainfall - 1400) / 4000
        noise = np.random.normal(0, 0.15)
        yield_per_ha = max(
            0.5,
            BASE_YIELD[crop] * temp_factor * rain_factor * (0.5 + 0.5 * (prev_yield / BASE_YIELD[crop])) + noise,
        )

        rows.append({
            "crop_name": crop,
            "area_ha": area,
            "avg_temperature": avg_temp,
            "total_rainfall": rainfall,
            "prev_season_yield": prev_yield,
            "yield_per_ha": round(yield_per_ha, 3),
        })
    return pd.DataFrame(rows)


def generate_price_history(days: int = 365) -> pd.DataFrame:
    rows = []
    start = date.today() - timedelta(days=days)
    for crop in CROPS:
        base = BASE_PRICE[crop]
        trend_slope = random.uniform(-3, 6)
        for i in range(days):
            d = start + timedelta(days=i)
            seasonal = 0.05 * base * np.sin(2 * np.pi * i / 90)
            noise = np.random.normal(0, base * 0.01)
            price = max(500, base + trend_slope * i * 0.05 + seasonal + noise)
            rows.append({"crop_name": crop, "date": d.isoformat(), "price": round(price, 0)})
    return pd.DataFrame(rows)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    yield_df = generate_yield_history()
    yield_df.to_csv(SAMPLE_YIELD_CSV, index=False)
    print(f"Đã ghi {len(yield_df)} dòng dữ liệu năng suất mẫu -> {SAMPLE_YIELD_CSV}")

    price_df = generate_price_history()
    price_df.to_csv(SAMPLE_PRICE_CSV, index=False)
    print(f"Đã ghi {len(price_df)} dòng dữ liệu giá mẫu -> {SAMPLE_PRICE_CSV}")


if __name__ == "__main__":
    main()
