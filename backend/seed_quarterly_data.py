"""
Seed thêm dữ liệu lịch sử cho các quý TRƯỚC để dashboard có QoQ, YoY khác 0%.
Script này KHÔNG drop bảng - chỉ thêm dữ liệu. Chạy nhiều lần vẫn an toàn (idempotent
theo (region.name, district) cho region và theo (district, crop_type, season) cho period).

Cách dùng trên Render:
    cd backend
    DATABASE_URL=postgresql://... python seed_quarterly_data.py
"""
import sys
import random
from datetime import date, datetime

# Fix Unicode on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.database import SessionLocal, engine
from app.models import Base, FarmingRegion, FarmingPeriod, DiseaseDetection, YieldPrediction

# Tên huyện KHỚP frontend/src/constants/districts.ts
FRONTEND_DISTRICTS = [
    "Điện Biên", "Điện Biên Đông", "Mường Ảng", "Mường Chà",
    "Mường Nhé", "Nậm Pồ", "Tủa Chùa", "Tuần Giáo",
]

DISEASES_BY_CROP = {
    "rice": [
        ("Đạo ôn lúa", "Pyricularia oryzae"),
        ("Bạc lá vi khuẩn", "Xanthomonas oryzae"),
        ("Khô vằn", "Rhizoctonia solani"),
    ],
    "coffee": [
        ("Gỉ sắt cà phê", "Hemileia vastatrix"),
        ("Sâu đục quả cà phê", "Hypothenemus hampei"),
        ("Thối rễ cà phê", "Fusarium spp."),
    ],
    "vegetable": [
        ("Sương mai rau màu", "Peronospora parasitica"),
        ("Rệp hại rau màu", "Aphidoidea"),
        ("Đốm lá rau màu", "Cercospora spp."),
    ],
}

# Quy luật "diễn biến" theo quý - mỗi quý có:
#   - n_regions: số vùng canh tác mới (tăng dần hoặc giảm tuỳ kịch bản)
#   - avg_area: diện tích trung bình / vùng
#   - yield_factor: hệ số năng suất (so với base)
#   - disease_count_per_region: số ca bệnh / vùng
# Thiết kế sao cho QoQ khác biệt rõ rệt.
SEASONAL_PATTERN = [
    # (q_offset, n_regions, avg_area, yield_factor, disease_per_region, label)
    (8,  2, 28, 0.55, 4,  "Q3/2024 (xuân, mưa ít)"),       # năng suất thấp, ít bệnh
    (7,  3, 32, 0.75, 3,  "Q4/2024 (thu, mưa vừa)"),       # năng suất tăng
    (6,  4, 30, 0.90, 5,  "Q1/2025 (đông, ít sâu bệnh)"),
    (5,  3, 35, 1.10, 4,  "Q2/2025 (xuân, thuận lợi)"),    # năng suất cao nhất
    (4,  5, 38, 1.20, 3,  "Q3/2025 (hè, nắng)"),
    (3,  4, 42, 1.05, 5,  "Q4/2025 (mùa mưa, nhiều bệnh)"),
    (2,  6, 45, 0.95, 4,  "Q1/2026 (đông, ổn định)"),
    (1,  5, 50, 1.15, 3,  "Q2/2026 (xuân, thuận lợi)"),    # kỳ trước - cao
    # q_offset=0 (Q3/2026) để TRỐNG cho demo cán bộ/nông dân tạo
]

BASE_YIELD = {"rice": 5.5, "coffee": 2.5, "vegetable": 12.0}
DENSITY_REF = 200.0


def quarter_year(today: date, q_offset: int):
    q_year = today.year
    q_num = (today.month - 1) // 3 + 1 - q_offset
    while q_num <= 0:
        q_num += 4
        q_year -= 1
    return q_year, q_num


def quarter_random_day(today: date, q_offset: int) -> date:
    q_year, q_num = quarter_year(today, q_offset)
    month = (q_num - 1) * 3 + random.randint(1, 3)
    return date(q_year, month, random.randint(1, 20))


def quarter_label(today: date, q_offset: int) -> str:
    q_year, q_num = quarter_year(today, q_offset)
    return f"Q{q_num}/{q_year}"


def region_exists(db, name: str) -> bool:
    return db.query(FarmingRegion).filter(FarmingRegion.name == name).first() is not None


def period_exists(db, region_id: int, crop_type: str) -> bool:
    return (
        db.query(FarmingPeriod)
        .filter(FarmingPeriod.region_id == region_id, FarmingPeriod.crop_type == crop_type)
        .first()
        is not None
    )


def run():
    random.seed(42)  # deterministic - chạy nhiều lần ra cùng kết quả

    # Tạo bảng nếu chưa có (idempotent cho DB mới)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    today = date.today()

    print(f"[*] Hôm nay: {today}")
    print(f"[*] Seed thêm dữ liệu cho các quý trước...")

    created_regions = 0
    created_periods = 0
    created_diseases = 0
    created_yields = 0
    skipped_regions = 0

    for q_off, n_regions, avg_area, yield_factor, disease_per_region, label in SEASONAL_PATTERN:
        ql = quarter_label(today, q_off)
        print(f"\n[*] {label} (q_offset={q_off}): {n_regions} vùng, diện tích TB {avg_area}ha, yield×{yield_factor}")

        for i in range(n_regions):
            dist = FRONTEND_DISTRICTS[i % len(FRONTEND_DISTRICTS)]
            region_name = f"Vùng canh tác {dist} ({ql}) #{i+1}"

            if region_exists(db, region_name):
                skipped_regions += 1
                continue

            created = quarter_random_day(today, q_off)
            area_ha = round(random.uniform(avg_area * 0.85, avg_area * 1.15), 1)

            region = FarmingRegion(
                name=region_name,
                district=dist,
                area_ha=area_ha,
                created_at=datetime.combine(created, datetime.min.time()),
            )
            db.add(region)
            db.flush()  # lấy region.id
            created_regions += 1

            # Mỗi vùng 1-2 vụ canh tác, mỗi vụ 1 crop_type
            crops_in_region = random.sample(["rice", "coffee", "vegetable"], k=random.randint(1, 2))
            for crop_type in crops_in_region:
                if period_exists(db, region.id, crop_type):
                    continue

                # Mật độ cây/ha dao động quanh REF, cho ra yield/ha dao động
                crop_count = random.randint(int(area_ha * DENSITY_REF * 0.8),
                                            int(area_ha * DENSITY_REF * 1.4))
                p_created = quarter_random_day(today, q_off)
                db.add(FarmingPeriod(
                    region_id=region.id,
                    crop_type=crop_type,
                    area_ha=area_ha,
                    crop_count=crop_count,
                    created_at=datetime.combine(p_created, datetime.min.time()),
                ))
                created_periods += 1

                # YieldPrediction cho từng (region, crop, quarter) - nông dân dự báo
                # Sẽ dùng cho frontend cũ và để tham chiếu
                base = BASE_YIELD[crop_type]
                # Yield/ha thực tế dao động do thời tiết
                yield_t_per_ha = base * yield_factor * random.uniform(0.9, 1.15)
                predicted_yield_tons = yield_t_per_ha * area_ha

                y_created = quarter_random_day(today, q_off)
                q_year, q_num = quarter_year(today, q_off)
                harvest = date(q_year, min(12, (q_num - 1) * 3 + random.randint(1, 3)),
                               random.randint(1, 28))
                db.add(YieldPrediction(
                    farm_id=None,  # hợp nhất với hệ thống mới
                    season=f"{q_year}-Q{q_num}",
                    predicted_yield=round(predicted_yield_tons, 2),
                    harvest_date=harvest,
                    created_at=datetime.combine(y_created, datetime.min.time()),
                ))
                created_yields += 1

            # Bệnh: theo crop_type có trong vùng
            for _ in range(disease_per_region):
                crop_type = random.choice(crops_in_region)
                disease_name, sci_name = random.choice(DISEASES_BY_CROP[crop_type])
                created = quarter_random_day(today, q_off)
                db.add(DiseaseDetection(
                    farm_id=None,
                    district=dist,
                    crop_type=crop_type,
                    image_url=f"/static/uploaded_images/disease_seed_{random.randint(1000, 9999)}.jpg",
                    disease_label=disease_name,
                    scientific_name=sci_name,
                    confidence=round(random.uniform(0.65, 0.95), 2),
                    severity=random.choice(["mild", "moderate", "severe"]),
                    affected_plant_count=random.randint(3, 50),
                    recommendation="Cách ly cây bệnh, phun thuốc phù hợp, theo dõi độ ẩm đất.",
                    created_at=datetime.combine(created, datetime.min.time()),
                    farming_region_id=region.id,
                ))
                created_diseases += 1

        db.commit()

    print("\n[*] HOÀN THÀNH!")
    print(f"   + Vùng canh tác mới: {created_regions} (bỏ qua {skipped_regions} đã tồn tại)")
    print(f"   + Vụ canh tác mới: {created_periods}")
    print(f"   + Báo cáo sâu bệnh mới: {created_diseases}")
    print(f"   + Dự báo năng suất mới: {created_yields}")
    print(f"\n[*] Tổng cộng trong DB:")
    print(f"   - Farming Regions: {db.query(FarmingRegion).count()}")
    print(f"   - Farming Periods: {db.query(FarmingPeriod).count()}")
    print(f"   - Disease Detections: {db.query(DiseaseDetection).count()}")
    print(f"   - Yield Predictions: {db.query(YieldPrediction).count()}")

    db.close()


if __name__ == "__main__":
    run()