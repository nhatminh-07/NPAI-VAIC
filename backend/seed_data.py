"""
Seed dữ liệu mẫu vào DB để dashboard có số liệu demo ngay khi chạy.

Chạy: python seed_data.py
"""
import random
from datetime import date, timedelta, datetime

from app.database import SessionLocal, Base, engine
from app.models import User, Crop, Farm, DiseaseDetection, YieldPrediction

random.seed(7)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

CROPS = [
    ("rice", "Vụ chiêm xuân + vụ mùa"),
    ("coffee", "Thu hoạch tháng 10-12"),
    ("vegetable", "Vụ đông, luân canh nhiều đợt/năm"),
]

LOCATIONS = ["Mường Ảng, Điện Biên", "Điện Biên Phủ, Điện Biên", "Tuần Giáo, Điện Biên", "Mường Chà, Điện Biên"]


def run():
    if db.query(Crop).count() == 0:
        for name, info in CROPS:
            db.add(Crop(name=name, season_info=info))
        db.commit()
        print("Đã tạo bảng Crops mẫu.")

    crops = {c.name: c for c in db.query(Crop).all()}

    if db.query(User).count() == 0:
        for i in range(1, 9):
            role = "officer" if i == 1 else "farmer"
            db.add(User(name=f"Người dùng {i}", role=role, phone=f"09{i:08d}"))
        db.commit()
        print("Đã tạo Users mẫu.")

    users = db.query(User).all()

    if db.query(Farm).count() == 0:
        for u in users:
            crop_name = random.choice(list(crops.keys()))
            farm = Farm(
                user_id=u.id,
                location=random.choice(LOCATIONS),
                area=round(random.uniform(0.5, 4.5), 2),
                crop_id=crops[crop_name].id,
            )
            db.add(farm)
        db.commit()
        print("Đã tạo Farms mẫu.")

    farms = db.query(Farm).all()

    if db.query(DiseaseDetection).count() == 0:
        labels = ["Đạo ôn lúa (Rice Blast)", "Gỉ sắt cà phê (Coffee Leaf Rust)", "Cây khỏe mạnh"]
        for farm in farms:
            for _ in range(random.randint(1, 4)):
                days_ago = random.randint(0, 200)
                db.add(DiseaseDetection(
                    farm_id=farm.id,
                    image_url="/static/uploaded_images/demo.jpg",
                    disease_label=random.choice(labels),
                    confidence=round(random.uniform(0.6, 0.95), 2),
                    recommendation="Xem gợi ý chi tiết trong API /detect-disease",
                    created_at=datetime.utcnow() - timedelta(days=days_ago),
                ))
        db.commit()
        print("Đã tạo DiseaseDetections mẫu.")

    if db.query(YieldPrediction).count() == 0:
        for farm in farms:
            for _ in range(random.randint(1, 3)):
                days_ago = random.randint(0, 200)
                created = datetime.utcnow() - timedelta(days=days_ago)
                harvest = created.date() + timedelta(days=100)
                quarter = (harvest.month - 1) // 3 + 1
                db.add(YieldPrediction(
                    farm_id=farm.id,
                    season=f"{harvest.year}-Q{quarter}",
                    predicted_yield=round(random.uniform(1.0, 20.0), 2),
                    harvest_date=harvest,
                    created_at=created,
                ))
        db.commit()
        print("Đã tạo YieldPredictions mẫu.")

    print("Seed dữ liệu hoàn tất.")


if __name__ == "__main__":
    run()
    db.close()
