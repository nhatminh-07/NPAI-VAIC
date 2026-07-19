"""
Router chạy seed script từ HTTP request (dùng cho deploy production trên Render,
vì free tier không có SSH). Chỉ cần gọi 1 lần sau deploy để seed dữ liệu.
"""
import random
from datetime import date, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.database import SessionLocal, engine
from app.models import Base, FarmingRegion, FarmingPeriod, DiseaseDetection, YieldPrediction

router = APIRouter(tags=["Seed"])

FRONTEND_DISTRICTS = [
    "Điện Biên", "Điện Biên Đông", "Mường Ảng", "Mường Chà",
    "Mường Nhé", "Nậm Pồ", "Tủa Chùa", "Tuần Giáo",
]

DISEASES_BY_CROP = {
    "rice": [("Đạo ôn lúa", "Pyricularia oryzae"), ("Bạc lá vi khuẩn", "Xanthomonas oryzae"), ("Khô vằn", "Rhizoctonia solani")],
    "coffee": [("Gỉ sắt cà phê", "Hemileia vastatrix"), ("Sâu đục quả cà phê", "Hypothenemus hampei"), ("Thối rễ cà phê", "Fusarium spp.")],
    "vegetable": [("Sương mai rau màu", "Peronospora parasitica"), ("Rệp hại rau màu", "Aphidoidea"), ("Đốm lá rau màu", "Cercospora spp.")],
}

# (q_offset, n_regions, avg_area, yield_factor, disease_per_region)
SEASONAL_PATTERN = [
    (9, 2, 28, 0.55, 4), (8, 3, 32, 0.75, 3),
    (7, 4, 30, 0.90, 5), (6, 3, 35, 1.10, 4),
    (5, 5, 38, 1.20, 3), (4, 4, 42, 1.05, 5),
    (3, 6, 45, 0.95, 4), (2, 5, 50, 1.15, 3),
    # Q3/2026 = quý hiện tại - vẫn seed để dashboard có data ngay khi deploy
    (0, 3, 40, 1.05, 4),
]

BASE_YIELD = {"rice": 5.5, "coffee": 2.5, "vegetable": 12.0}
DENSITY_REF = 200.0


def _quarter_year(today, q_offset):
    q_year = today.year
    q_num = (today.month - 1) // 3 + 1 - q_offset
    while q_num <= 0:
        q_num += 4
        q_year -= 1
    return q_year, q_num


def _quarter_label(today, q_offset):
    q_year, q_num = _quarter_year(today, q_offset)
    return f"Q{q_num}/{q_year}"


def _quarter_random_day(today, q_offset):
    q_year, q_num = _quarter_year(today, q_offset)
    month = (q_num - 1) * 3 + random.randint(1, 3)
    return date(q_year, month, random.randint(1, 20))


class SeedResponse(BaseModel):
    message: str
    regions: int
    periods: int
    diseases: int
    yields: int
    severity_updated: int
    total_regions: int
    total_periods: int
    total_diseases: int
    total_yields: int


@router.post("/seed", response_model=SeedResponse)
def seed_all():
    """Seed dữ liệu quý cho dashboard. Gọi 1 lần sau deploy."""
    random.seed(42)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    today = date.today()

    created_regions = created_periods = created_diseases = created_yields = 0
    severity_updated = 0
    skipped = 0

    # Backfill severity cho TẤT CẢ disease_detections (cũ + mới) — phân bố 30/50/20.
    # Cập nhật cả những dòng đã có severity hợp lệ để tránh data cũ bị "Trung bình" đồng loạt.
    SEVERITY_DIST = ["mild"] * 3 + ["moderate"] * 5 + ["severe"] * 2
    old_diseases = db.query(DiseaseDetection).all()
    for d in old_diseases:
        d.severity = random.choice(SEVERITY_DIST)
        # affected_plant_count cũng đang 0 hết do seed cũ không set - bổ sung luôn
        if not d.affected_plant_count or d.affected_plant_count == 0:
            d.affected_plant_count = random.randint(3, 50)
        severity_updated += 1
    if severity_updated:
        db.commit()

    for q_off, n_regions, avg_area, yield_factor, disease_per_region in SEASONAL_PATTERN:
        ql = _quarter_label(today, q_off)
        for i in range(n_regions):
            dist = FRONTEND_DISTRICTS[i % len(FRONTEND_DISTRICTS)]
            region_name = f"Vùng canh tác {dist} ({ql}) #{i+1}"

            if db.query(FarmingRegion).filter(FarmingRegion.name == region_name).first():
                skipped += 1
                continue

            created = _quarter_random_day(today, q_off)
            area_ha = round(random.uniform(avg_area * 0.85, avg_area * 1.15), 1)
            region = FarmingRegion(
                name=region_name, district=dist, area_ha=area_ha,
                created_at=datetime.combine(created, datetime.min.time()),
            )
            db.add(region)
            db.flush()
            created_regions += 1

            crops_in_region = random.sample(["rice", "coffee", "vegetable"], k=random.randint(1, 2))
            for crop_type in crops_in_region:
                if db.query(FarmingPeriod).filter(
                    FarmingPeriod.region_id == region.id, FarmingPeriod.crop_type == crop_type
                ).first():
                    continue

                crop_count = random.randint(int(area_ha * DENSITY_REF * 0.8), int(area_ha * DENSITY_REF * 1.4))
                db.add(FarmingPeriod(
                    region_id=region.id, crop_type=crop_type, area_ha=area_ha,
                    crop_count=crop_count,
                    created_at=datetime.combine(_quarter_random_day(today, q_off), datetime.min.time()),
                ))
                created_periods += 1

                base = BASE_YIELD[crop_type]
                yield_t_per_ha = base * yield_factor * random.uniform(0.9, 1.15)
                q_year, q_num = _quarter_year(today, q_off)
                db.add(YieldPrediction(
                    farm_id=None, season=f"{q_year}-Q{q_num}",
                    predicted_yield=round(yield_t_per_ha * area_ha, 2),
                    harvest_date=date(q_year, min(12, (q_num - 1) * 3 + random.randint(1, 3)), random.randint(1, 28)),
                    created_at=datetime.combine(_quarter_random_day(today, q_off), datetime.min.time()),
                ))
                created_yields += 1

            for _ in range(disease_per_region):
                crop_type = random.choice(crops_in_region)
                disease_name, sci_name = random.choice(DISEASES_BY_CROP[crop_type])
                db.add(DiseaseDetection(
                    farm_id=None, district=dist, crop_type=crop_type,
                    image_url=f"/static/uploaded_images/disease_seed_{random.randint(1000, 9999)}.jpg",
                    disease_label=disease_name, scientific_name=sci_name,
                    confidence=round(random.uniform(0.65, 0.95), 2),
                    severity=random.choice(["mild", "moderate", "severe"]),
                    affected_plant_count=random.randint(3, 50),
                    recommendation="Cách ly cây bệnh, phun thuốc phù hợp.",
                    created_at=datetime.combine(_quarter_random_day(today, q_off), datetime.min.time()),
                    farming_region_id=region.id,
                ))
                created_diseases += 1

        db.commit()

    total_regions = db.query(FarmingRegion).count()
    total_periods = db.query(FarmingPeriod).count()
    total_diseases = db.query(DiseaseDetection).count()
    total_yields = db.query(YieldPrediction).count()
    db.close()

    return SeedResponse(
        message=f"Đã tạo {created_regions} vùng, {created_periods} vụ, {created_diseases} báo cáo bệnh, {created_yields} dự báo (bỏ qua {skipped} trùng), cập nhật severity {severity_updated} báo cáo cũ",
        regions=created_regions, periods=created_periods,
        diseases=created_diseases, yields=created_yields,
        severity_updated=severity_updated,
        total_regions=total_regions, total_periods=total_periods,
        total_diseases=total_diseases, total_yields=total_yields,
    )
