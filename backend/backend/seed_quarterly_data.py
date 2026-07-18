"""
Seed thêm dữ liệu đa dạng theo quý để dashboard có dữ liệu demo.
Chạy: python seed_quarterly_data.py
"""
import random
from datetime import date, timedelta, datetime

from app.database import SessionLocal, Base, engine
from app.models import User, Crop, Farm, DiseaseDetection, YieldPrediction

random.seed(42)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

LOCATIONS = ["Mường Ảng, Điện Biên", "Điện Biên Phủ, Điện Biên", "Tuần Giáo, Điện Biên", "Mường Chà, Điện Biên"]
DISEASE_LABELS = [
    "Đạo ôn lúa (Rice Blast)",
    "Bạc lá vi khuẩn (Bacterial Leaf Blight)",
    "Gỉ sắt cà phê (Coffee Leaf Rust)",
    "Sâu đục quả cà phê (Coffee Berry Borer)",
    "Sương mai rau màu (Downy Mildew)",
    "Rệp hại rau màu (Aphids)",
    "Cây khỏe mạnh",
]


def add_quarterly_data(start_year=2025, quarters=8):
    """Thêm dữ liệu cho nhiều quý."""
    farms = db.query(Farm).all()
    if not farms:
        print("Chưa có farm. Chạy seed_data.py trước.")
        return

    existing_yields = db.query(YieldPrediction).count()
    existing_diseases = db.query(DiseaseDetection).count()

    added_yields = 0
    added_diseases = 0

    # YieldPredictions cho mỗi quý
    year = start_year
    quarter = 1
    for _ in range(quarters):
        for farm in farms:
            if random.random() < 0.6:  # 60% farms có prediction mỗi quý
                start_month = (quarter - 1) * 3 + 1
                created_date = date(year, start_month, 5)
                harvest_date = created_date + timedelta(days=random.randint(80, 120))
                harvest_quarter = (harvest_date.month - 1) // 3 + 1
                harvest_year = harvest_date.year

                db.add(YieldPrediction(
                    farm_id=farm.id,
                    season=f"{harvest_year}-Q{harvest_quarter}",
                    predicted_yield=round(random.uniform(2.0, 18.0), 2),
                    harvest_date=harvest_date,
                    created_at=datetime.combine(created_date, datetime.min.time()),
                ))
                added_yields += 1

                # Disease detections
                if random.random() < 0.5:
                    for _ in range(random.randint(1, 3)):
                        db.add(DiseaseDetection(
                            farm_id=farm.id,
                            district=farm.location,
                            crop_type=farm.crop.name if farm.crop else "rice",
                            image_url="/static/uploaded_images/demo.jpg",
                            disease_label=random.choice(DISEASE_LABELS),
                            confidence=round(random.uniform(0.6, 0.95), 2),
                            recommendation="Xem gợi ý chi tiết trong API /disease/detect",
                            created_at=datetime.combine(created_date, datetime.min.time()),
                        ))
                        added_diseases += 1

        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1

    db.commit()
    print(f"Đã thêm: {added_yields} YieldPredictions, {added_diseases} DiseaseDetections")
    print(f"Tổng: {db.query(YieldPrediction).count()} YieldPredictions, {db.query(DiseaseDetection).count()} DiseaseDetections")


if __name__ == "__main__":
    add_quarterly_data()
    db.close()
