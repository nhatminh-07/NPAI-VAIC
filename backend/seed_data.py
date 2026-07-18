"""
Seed dữ liệu mẫu vào DB để dashboard có số liệu demo ngay khi chạy.
Dữ liệu thay đổi theo ngày hiện tại để demo realistic.

Chạy: python seed_data.py
"""
import random
import sys
from datetime import date, timedelta, datetime

# Fix Unicode on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.database import SessionLocal, Base, engine
from app.models import Crop, Farm, DiseaseDetection, YieldPrediction, FarmingRegion, FarmingPeriod

random.seed()

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Quận/huyện Điện Biên (dùng cho dữ liệu Farm cũ - có tiền tố)
DISTRICTS = [
    "Thành phố Điện Biên Phủ",
    "Huyện Tuần Giáo",
    "Huyện Mường Chà",
    "Huyện Tủa Chùa",
    "Huyện Mường Nhé",
    "Huyện Điện Biên Đông",
    "Huyện Mường Ảng",
    "Huyện Nậm Pồ",
]

# Tên huyện KHỚP frontend/src/constants/districts.ts (KHÔNG tiền tố) - dùng cho hệ thống
# vùng canh tác mới, để dữ liệu seed và dữ liệu cán bộ tạo qua UI dùng chung 1 chuẩn tên.
FRONTEND_DISTRICTS = [
    "Điện Biên", "Điện Biên Đông", "Mường Ảng", "Mường Chà",
    "Mường Nhé", "Nậm Pồ", "Tủa Chùa", "Tuần Giáo",
]

# Bệnh theo loại cây (tên tiếng Việt + tên khoa học) - dùng cho báo cáo sâu bệnh gắn vùng.
DISEASES_BY_CROP = {
    "rice": [("Đạo ôn lúa", "Pyricularia oryzae"), ("Bạc lá vi khuẩn", "Xanthomonas oryzae")],
    "coffee": [("Gỉ sắt cà phê", "Hemileia vastatrix"), ("Sâu đục quả cà phê", "Hypothenemus hampei")],
    "vegetable": [("Sương mai rau màu", "Peronospora parasitica"), ("Rệp hại rau màu", "Aphidoidea")],
}
SEVERITIES = ["mild", "moderate", "severe"]

# Tên nông dân giả
FARMER_NAMES = [
    "Nguyễn Văn Minh", "Trần Thị Lan", "Lê Văn Hùng", "Phạm Thị Hương",
    "Hoàng Văn Tâm", "Ngô Thị Mai", "Đặng Văn Phúc", "Bùi Thị Thu",
    "Đỗ Văn Quang", "Lý Thị Hồng", "Mã Văn Đức", "Hà Thị Nga",
    "Cao Văn Lâm", "Đinh Thị Phương", "Nguyễn Văn Thắng", "Trịnh Thị Yến",
]

# Bệnh cây trồng
DISEASES = [
    ("Đạo ôn lúa", "rice", 0.25),
    ("Bạc lá vi khuẩn", "rice", 0.20),
    ("Sương mai rau màu", "vegetable", 0.18),
    ("Rệp hại rau màu", "vegetable", 0.15),
    ("Gỉ sắt cà phê", "coffee", 0.12),
    ("Sâu đục quả cà phê", "coffee", 0.10),
    ("Cây khỏe mạnh", "rice", 0.30),
    ("Cây khỏe mạnh", "vegetable", 0.25),
    ("Cây khỏe mạnh", "coffee", 0.20),
]

# Lý do theo thời tiết (thay đổi theo ngày)
WEATHER_REASONS = {
    "rainy": [
        "Do mưa nhiều liên tục trong tuần qua, độ ẩm tăng cao tạo điều kiện cho nấm bệnh phát triển.",
        "Lượng mưa lớn khiến nước đọng trên lá, vi khuẩn dễ xâm nhập.",
        "Trời mưa liên tục, nông dân không thể phun thuốc phòng trừ kịp thời.",
        "Độ ẩm cao kết hợp nhiệt độ ấm là môi trường lý tưởng cho sâu bệnh.",
        "Mưa kéo dài gây ngập úng cục bộ, rễ cây thiếu oxy.",
    ],
    "hot": [
        "Nắng nóng kéo dài, cây thiếu nước, sức đề kháng giảm.",
        "Nhiệt độ cao trên 35°C khiến lá cây bị vàng và hoại tử.",
        "Trời nắng nóng, tưới không đủ khiến cây dễ bị sâu bệnh tấn công.",
        "Độ ẩm thấp trong ngày nắng nóng làm cây stress và dễ nhiễm bệnh.",
        "Cây bị cháy nắng ở vùng lá non do nhiệt độ quá cao.",
    ],
    "humid": [
        "Sương mù buổi sáng kéo dài, tạo điều kiện cho nấm bệnh phát triển.",
        "Độ ẩm ban đêm cao trên 90%, sáng sớm có sương mù.",
        "Thời tiết âm u, thiếu ánh nắng khiến cây yếu.",
        "Buổi sáng có sương mù, trưa nắng nhẹ, độ ẩm cao cả ngày.",
        "Độ ẩm cao khiến lá cây bị ố vàng, côn trùng phát triển mạnh.",
    ],
    "stormy": [
        "Sau cơn bão, cây bị gãy cành, vết thương là cửa ngõ cho vi khuẩn.",
        "Gió mạnh và mưa to trong đợt bão gần đây khiến sâu bệnh lây lan nhanh.",
        "Cơn bão vừa qua để lại nhiều cây đổ ngã, cần kiểm tra sức khỏe cây trồng.",
        "Mưa kèm gió giật mạnh làm lá bị rách, dễ nhiễm nấm bệnh.",
        "Bão gây mất lá, cây suy yếu nghiêm trọng và dễ nhiễm bệnh thứ phát.",
    ],
}

LOW_YIELD_REASONS = [
    "Do thời tiết bất lợi trong kỳ sinh trưởng",
    "Đất canh tác thiếu dinh dưỡng sau nhiều vụ liên tục",
    "Sâu bệnh hoành hành trong giai đoạn ra hoa",
    "Hạn hán kéo dài ảnh hưởng đến quá trình tăng trưởng",
    "Mưa acid gây ảnh hưởng đến quang hợp của cây",
    "Độ ẩm không phù hợp trong giai đoạn trổ bông",
]

HIGH_YIELD_REASONS = [
    "Thời tiết thuận lợi, nắng ấm vừa phải và mưa đều",
    "Đất đai được bón phân đầy đủ và cải tạo tốt",
    "Nông dân áp dụng kỹ thuật canh tác tiên tiến",
    "Giống cây trồng chất lượng cao, kháng bệnh tốt",
    "Hệ thống tưới tiêu hoạt động hiệu quả",
]


def get_weather_condition(day_offset: int = 0) -> str:
    """Xác định điều kiện thời tiết dựa trên ngày (để demo thay đổi theo ngày)."""
    seed = (date.today().toordinal() + day_offset) % 30
    if seed < 8:
        return "rainy"
    elif seed < 14:
        return "hot"
    elif seed < 22:
        return "humid"
    else:
        return "stormy"


def get_disease_factor(weather: str) -> float:
    """Factor nhân cho bệnh dựa trên thời tiết."""
    factors = {"rainy": 1.5, "hot": 0.7, "humid": 1.2, "stormy": 1.8}
    return factors.get(weather, 1.0)


def run():
    print("[*] Xoa du lieu cu...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    today = date.today()
    weather = get_weather_condition()

    print(f"\n[*] Ngay hien tai: {today}")
    print(f"[*] Thoi tiet: {weather.upper()}")
    print(f"[*] Factor benh: x{get_disease_factor(weather)}")

    # Tạo crops
    print("\n[*] Tao cay trong...")
    crops_data = [
        ("rice", "Vụ chiêm xuân + vụ mùa"),
        ("coffee", "Thu hoạch tháng 10-12"),
        ("vegetable", "Vụ đông, luân canh nhiều đợt/năm"),
    ]
    crops = {}
    for name, season in crops_data:
        crop = Crop(name=name, season_info=season)
        db.add(crop)
        crops[name] = crop
    db.commit()

    db.commit()

    # Tạo farms (cần user_id)
    print("[*] Tao trang trai...")
    farms = []

    # Tạo user trước
    from app.models import User
    users = []
    for i, farmer in enumerate(FARMER_NAMES):
        user = User(name=farmer, role="farmer", phone=f"09{i:08d}")
        db.add(user)
        users.append(user)
    db.commit()

    for i, farmer in enumerate(FARMER_NAMES):
        district = DISTRICTS[i % len(DISTRICTS)]
        crop_name = ["rice", "coffee", "vegetable"][i % 3]
        area = round(random.uniform(0.5, 5.0), 2)

        farm = Farm(
            user_id=users[i].id,
            location=district,
            area=area,
            crop_id=crops[crop_name].id,
        )
        db.add(farm)
        farms.append(farm)

    db.commit()

    # Tạo yield predictions cho 4 quý gần nhất
    print("[*] Tao du lieu nang suat...")

    base_yields = {"rice": 5.5, "coffee": 2.5, "vegetable": 12.0}

    for farm in farms:
        for q in range(4):
            q_year = today.year
            q_num = (today.month - 1) // 3 + 1 - q
            while q_num <= 0:
                q_num += 4
                q_year -= 1

            q_weather = get_weather_condition(q)
            weather_factor = 0.85 + random.uniform(0, 0.3)
            if q_weather == "rainy":
                weather_factor *= 0.9
            elif q_weather == "hot":
                weather_factor *= 0.85
            elif q_weather == "stormy":
                weather_factor *= 0.8

            base = base_yields.get(farm.crop.name, 5.0)
            predicted_yield = round(base * weather_factor * farm.area * random.uniform(0.9, 1.1), 2)

            # Spread created_at thực sự vào từng quý (tháng giữa quý, ngày random)
            # Để dashboard filter theo created_at sẽ ra dữ liệu cho từng kỳ
            q_mid_month = (q_num - 1) * 3 + random.randint(1, 3)
            q_created_day = random.randint(5, 25)
            yield_created_at = datetime(q_year, q_mid_month, q_created_day, random.randint(8, 17), random.randint(0, 59))

            harvest_date = date(q_year, (q_num - 1) * 3 + random.randint(1, 3), random.randint(1, 28))
            season = f"{q_year}-Q{q_num}"

            yield_pred = YieldPrediction(
                farm_id=farm.id,
                season=season,
                predicted_yield=predicted_yield,
                harvest_date=harvest_date,
                created_at=yield_created_at,
            )
            db.add(yield_pred)

    db.commit()

    # ==================================================================================
    # HỆ THỐNG QUẢN LÝ (hợp nhất): Vùng canh tác -> Vụ canh tác -> Báo cáo sâu bệnh.
    # Toàn bộ dashboard đọc từ đây (xem app/routers/frontend_dashboard.py).
    #
    # QUAN TRỌNG cho DEMO: mỗi KỲ (quý) có dữ liệu RIÊNG, và QUÝ HIỆN TẠI (Quý 3/2026 khi
    # demo) được để TRỐNG cố ý - chỉ seed 3 quý TRƯỚC (q_off 3,2,1 = Q4/2025, Q1/2026,
    # Q2/2026). Trong lúc demo, cán bộ/nông dân tạo dữ liệu mới -> created_at = bây giờ =
    # quý hiện tại -> quý hiện tại dần được lấp đầy trực tiếp trên dashboard.
    # ==================================================================================
    def quarter_day(q_offset):
        """1 ngày ngẫu nhiên nằm trong quý cách quý hiện tại `q_offset` quý về trước."""
        q_year = today.year
        q_num = (today.month - 1) // 3 + 1 - q_offset
        while q_num <= 0:
            q_num += 4
            q_year -= 1
        month = (q_num - 1) * 3 + random.randint(1, 3)
        return date(q_year, month, random.randint(1, 20))

    # Số vùng canh tác cho từng quý trước -> tổng diện tích KHÁC NHAU rõ giữa các kỳ
    # (Q4/2025: 3 vùng, Q1/2026: 4 vùng, Q2/2026: 5 vùng). Quý hiện tại (q_off=0): 0 vùng.
    TERMS_TO_SEED = {3: 3, 2: 4, 1: 5}

    def quarter_label(q_offset):
        """Nhãn quý dạng 'Q2/2026' cho quý cách quý hiện tại q_offset quý."""
        q_year = today.year
        q_num = (today.month - 1) // 3 + 1 - q_offset
        while q_num <= 0:
            q_num += 4
            q_year -= 1
        return f"Q{q_num}/{q_year}"

    print("[*] Tao vung canh tac (cac quy truoc, chua co Q hien tai)...")
    regions = []  # list[(FarmingRegion, q_off)]
    for q_off, n_regions in TERMS_TO_SEED.items():
        qlabel = quarter_label(q_off)
        for i in range(n_regions):
            dist = FRONTEND_DISTRICTS[i % len(FRONTEND_DISTRICTS)]
            created = quarter_day(q_off)
            region = FarmingRegion(
                name=f"Vùng canh tác {dist} ({qlabel})",
                district=dist,
                area_ha=round(random.uniform(25, 60), 1),
                created_at=datetime.combine(created, datetime.min.time()),
            )
            db.add(region)
            regions.append((region, q_off))
    db.commit()

    # --- Vụ canh tác: mỗi vùng 1-2 vụ, CÙNG quý với vùng ---
    print("[*] Tao vu canh tac...")
    region_crops = {}  # region_id -> danh sách crop_type để gắn bệnh cho đúng cây
    for region, q_off in regions:
        crops_here = []
        for _ in range(random.randint(1, 2)):
            crop_type = random.choice(["rice", "coffee", "vegetable"])
            crops_here.append(crop_type)
            created = quarter_day(q_off)
            db.add(FarmingPeriod(
                region_id=region.id,
                crop_type=crop_type,
                area_ha=round(random.uniform(2, 8), 1),
                crop_count=random.randint(100, 2000),
                created_at=datetime.combine(created, datetime.min.time()),
            ))
        region_crops[region.id] = crops_here or ["rice"]
    db.commit()

            q_mid_month = (q_num - 1) * 3 + random.randint(1, 3)
            q_day = random.randint(5, 25)
            d_created_at = datetime(q_year, q_mid_month, q_day, random.randint(8, 17), random.randint(0, 59))

            detection = DiseaseDetection(
                farm_id=farm.id,
                image_url=f"/static/uploaded_images/disease_{random.randint(1,100)}.jpg",
                disease_label=disease_name,
                scientific_name=sci_name,
                confidence=round(random.uniform(0.6, 0.95), 2),
                recommendation=reason,
                crop_type=crop_type,
                district=farm.location,
                created_at=d_created_at,
            )
            db.add(detection)

    db.commit()

    # Thống kê
    print("\n[*] HOAN THANH! Thong ke du lieu:")
    print(f"   - Farms: {db.query(Farm).count()}")
    print(f"   - Yield Predictions: {db.query(YieldPrediction).count()}")
    print(f"   - Farming Regions: {db.query(FarmingRegion).count()}")
    print(f"   - Farming Periods: {db.query(FarmingPeriod).count()}")
    print(f"   - Disease Detections: {db.query(DiseaseDetection).count()}")
    print(f"\n   Thoi tiet hien tai: {weather.upper()}")


if __name__ == "__main__":
    run()
    db.close()
