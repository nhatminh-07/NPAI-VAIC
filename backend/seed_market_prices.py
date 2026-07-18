"""
Seed dữ liệu giá thị trường thực tế (1/6 - 16/7/2026) vào bảng MarketPrice trong DB.

Dữ liệu: dien_bien_crop_prices.csv (wide format)
  - coffee_price_vnd_kg       -> rice (lúa Bắc Thơm 7)
  - bac_thom_7_price_vnd_kg   -> coffee (cà phê)
  - tomato_price_vnd_kg       -> vegetable (cà chua)

Lưu ý: crop_name trong CSV giữ nguyên tên gốc để map đúng:
  - "rice"    = Bắc Thơm số 7 (lúa)    -> model Crop.name = "rice"
  - "coffee"  = cà phê robusta           -> model Crop.name = "coffee"
  - "vegetable" = cà chua                -> model Crop.name = "vegetable"

Chạy: python seed_market_prices.py
"""

import sys
import pandas as pd
from datetime import date

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.database import SessionLocal
from app.models import Crop, MarketPrice
from app.config import BASE_DIR

CSV_PATH = f"{BASE_DIR}/app/data/gia_thi_truong_2026.csv"


def run():
    print("[*] Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")

    print(f"[*] Found {len(df)} rows, date range: {df['date'].min().date()} → {df['date'].max().date()}")

    # Map wide columns -> crop names (matching Crop.name in DB)
    col_to_crop = {
        "bac_thom_7_price_vnd_kg": "rice",
        "coffee_price_vnd_kg": "coffee",
        "tomato_price_vnd_kg": "vegetable",
    }

    db = SessionLocal()
    try:
        # Tạo/update crops
        crop_names = list(col_to_crop.values())
        for name in crop_names:
            existing = db.query(Crop).filter(Crop.name == name).first()
            if not existing:
                crop = Crop(name=name, season_info="dien_bien_crops_ml.csv")
                db.add(crop)
                print(f"  [+] Created crop: {name}")
            else:
                print(f"  [=] Crop exists: {name}")

        db.commit()

        # Seed market prices
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            for col, crop_name in col_to_crop.items():
                if col not in row:
                    continue
                price_val = row[col]
                if pd.isna(price_val):
                    continue

                crop = db.query(Crop).filter(Crop.name == crop_name).first()
                if not crop:
                    print(f"  [!] Crop not found: {crop_name}")
                    continue

                # Check duplicate
                existing = db.query(MarketPrice).filter(
                    MarketPrice.crop_id == crop.id,
                    MarketPrice.date == row["date"].date()
                ).first()

                if existing:
                    existing.price = float(price_val)
                    existing.source = "dien_bien_crop_prices.csv"
                    skipped += 1
                else:
                    mp = MarketPrice(
                        crop_id=crop.id,
                        date=row["date"].date(),
                        price=float(price_val),
                        source="dien_bien_crop_prices.csv",
                    )
                    db.add(mp)
                    inserted += 1

        db.commit()

        # Summary
        total = db.query(MarketPrice).count()
        by_crop = {}
        for name in crop_names:
            crop = db.query(Crop).filter(Crop.name == name).first()
            if crop:
                by_crop[name] = db.query(MarketPrice).filter(MarketPrice.crop_id == crop.id).count()

        print(f"\n[*] DONE!")
        print(f"  Total records in DB: {total}")
        print(f"  New inserted: {inserted}")
        print(f"  Updated: {skipped}")
        for name, count in by_crop.items():
            print(f"    - {name}: {count} records")

    finally:
        db.close()


if __name__ == "__main__":
    run()
