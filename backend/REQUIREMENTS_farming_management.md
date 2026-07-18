# Yêu cầu backend/DB: Quản lý vùng canh tác & vụ canh tác

Tài liệu này mô tả đầy đủ những gì backend cần làm để hỗ trợ tính năng "Quản lý"
(officer tạo vùng canh tác, farmer khai báo vụ canh tác) mà frontend đã build sẵn ở
`frontend/src/app/(officer)/management/page.tsx` và
`frontend/src/app/(farmer)/farming-periods/page.tsx`. Contract JSON đầy đủ đã có ở
`frontend/src/lib/api.ts` (đoạn "GHI CHÚ CHO BACKEND ENGINEER") - tài liệu này bổ sung
phần **quan trọng nhất**: cách tính năng mới ăn khớp với các phép tính hiện có ở
dashboard (đặc biệt là "Tổng diện tích" và "Tỷ lệ sâu bệnh"), để không tạo ra 2 nguồn
sự thật (source of truth) cho "diện tích đang canh tác" song song nhau.

**Không đổi gì ở frontend hay backend trong tài liệu này** - đây thuần là spec để backend
engineer triển khai. Không migrate/xoá dữ liệu hiện có.

---

## 1. Hiện trạng (đọc trực tiếp từ code, không suy đoán)

### 1.1 Bảng liên quan hiện có (`app/models.py`)

- `Farm`: `user_id` (NOT NULL, không có auth thật nên luôn phải seed giả),
  `location` (string tự do, vd `"Huyện Tuần Giáo"`), `area` (ha), `crop_id`.
- `DiseaseDetection`: có `farm_id` (nullable) VÀ `district` (string tự do, độc lập với
  Farm) - báo cáo qua `/disease/detect` (officer/farmer chẩn đoán) luôn để `farm_id=NULL`,
  chỉ ghi `district` dạng text nhập tay từ danh sách huyện của **frontend**.
- `YieldPrediction`: `farm_id` (NOT NULL), `predicted_yield`, `created_at`.

### 1.2 `GET /dashboard` tính KPI như thế nào (`app/routers/frontend_dashboard.py`)

| KPI | Công thức thực tế trong code | Vấn đề |
|---|---|---|
| **Tổng diện tích** (`total_area_ha`) | `SUM(Farm.area)`, lọc theo `crop_id` nếu có | **Không lọc theo khoảng thời gian** dù hàm nhận tham số `start/end` - luôn cộng TOÀN BỘ farm hiện có bất kể kỳ nào. Hệ quả: `qoqDeltaPercent` của KPI này **luôn = 0%** vì kỳ hiện tại và kỳ trước dùng chung 1 query giống hệt nhau. |
| **Năng suất trung bình** | `AVG(YieldPrediction.predicted_yield)` trong khoảng thời gian, join `Farm` | `YieldPrediction` **chỉ được tạo bởi `seed_data.py`** (4 quý giả cho mỗi farm seed). Endpoint `POST /yield/predict` (farmer dùng ở trang /forecast) là **stateless** - không hề `db.add()` - nên mọi dự báo thật của farmer **không bao giờ chảy vào dashboard**. |
| **Số ca sâu bệnh** | `COUNT(DiseaseDetection)` trong khoảng thời gian | Đúng, cộng dồn theo `created_at`. |
| **Tỷ lệ sâu bệnh** (`disease_rate_percent`) | `disease_count / total_farms_count * 100` | ⚠️ **Đây là điểm quan trọng nhất cho tài liệu này.** Công thức hiện tại **KHÔNG liên quan gì đến diện tích** - mẫu số là **SỐ LƯỢNG farm** (đếm bản ghi), không phải **DIỆN TÍCH**. Vd 3 ca bệnh / 8 farm = 37.5%, con số này không nói lên "% diện tích bị ảnh hưởng" như tên field gợi ý. |
| **Năng suất/Xếp hạng theo huyện** | Group theo `Farm.location` (text tự do), join `YieldPrediction` | Vì `YieldPrediction` chỉ có dữ liệu seed, các số này **tĩnh, không phản ánh hoạt động thật**. |

Ngoài ra có `app/services/dashboard_service.py` - **code trùng lặp gần như y hệt**
`frontend_dashboard.py` nhưng không được router nào gọi (dead code, có lẽ là bản nháp
trước khi viết `frontend_dashboard.py`). Nên dọn hoặc hợp nhất khi sửa, kẻo sửa 1 chỗ
quên chỗ kia.

### 1.3 Phát hiện thêm: huyện không khớp giữa frontend và seed data

- `frontend/src/constants/districts.ts`: `"Điện Biên"`, `"Tuần Giáo"`, `"Mường Ảng"`, ...
  (không tiền tố).
- `backend/seed_data.py` (`DISTRICTS`): `"Thành phố Điện Biên Phủ"`, `"Huyện Tuần Giáo"`,
  `"Huyện Mường Ảng"`, ... (có tiền tố "Huyện"/"Thành phố").

**2 danh sách này không match 1-1.** Nếu `FarmingRegion.district` lưu theo giá trị
frontend gửi lên (không tiền tố) mà so sánh/group chung với `Farm.location` hay
`DiseaseDetection.district` (có tiền tố, từ seed data cũ), các phép JOIN/GROUP BY theo
huyện sẽ **âm thầm không khớp**. Cần chuẩn hoá 1 trong 2 phía trước khi dùng
`FarmingRegion.district` để join với dữ liệu cũ. Khuyến nghị: đổi seed data hoặc thêm 1
bước chuẩn hoá (strip "Huyện "/"Thành phố ") khi so sánh - **không đổi
`constants/districts.ts` phía frontend** vì đó là danh sách hiển thị cho người dùng.

---

## 2. Schema đề xuất (thuần cộng thêm - không sửa bảng cũ)

```python
class FarmingRegion(Base):
    """Vùng canh tác do cán bộ nông nghiệp tạo - 1 khu vực thuộc 1 huyện của Điện Biên."""
    __tablename__ = "farming_regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)          # vd "Vùng lúa Mường Ảng 1"
    district = Column(String, nullable=False)       # PHẢI dùng đúng giá trị trong
                                                      # frontend/src/constants/districts.ts
    area_ha = Column(Float, nullable=False)          # diện tích TOÀN VÙNG cán bộ khoanh định
    created_at = Column(DateTime, default=datetime.utcnow)

    periods = relationship("FarmingPeriod", back_populates="region")


class FarmingPeriod(Base):
    """1 vụ canh tác nông dân khai báo, nằm trong 1 FarmingRegion có sẵn."""
    __tablename__ = "farming_periods"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("farming_regions.id"), nullable=True)
    crop_type = Column(String, nullable=False)       # rice | coffee | vegetable
    area_ha = Column(Float, nullable=False)           # diện tích THỰC TẾ đang canh tác
                                                        # trong vụ này (<= area_ha của region,
                                                        # không cần ràng buộc cứng ở DB, nhưng
                                                        # nên validate ở API layer)
    crop_count = Column(Integer, nullable=True)       # số lượng cây trồng
    created_at = Column(DateTime, default=datetime.utcnow)

    region = relationship("FarmingRegion", back_populates="periods")
```

### 2.1 Thêm 1 cột (không phá gì) vào `DiseaseDetection` - **để tính tỷ lệ sâu bệnh theo diện tích**

```python
class DiseaseDetection(Base):
    ...
    farming_period_id = Column(Integer, ForeignKey("farming_periods.id"), nullable=True)
    # nullable vì các báo cáo cũ (trước khi có tính năng này) và báo cáo không gắn vụ cụ
    # thể vẫn phải hoạt động bình thường - KHÔNG bắt buộc điền.
```

Đây là mắt xích còn thiếu: hiện `DiseaseDetection` chỉ có `district` (text tự do), không
biết ca bệnh đó thuộc vụ canh tác nào → không biết diện tích liên quan → không thể tính
"% diện tích bị ảnh hưởng". Có `farming_period_id`, ta mới lấy được `area_ha` của vụ đó.

Cập nhật tương ứng ở `POST /disease/detect` (file `frontend_disease.py`): thêm field
form tuỳ chọn `farmingPeriodId` (không bắt buộc, để tương thích ngược - nông dân chưa
khai vụ canh tác vẫn báo cáo bệnh được như cũ).

---

## 3. Đề xuất sửa công thức dashboard (phần quan trọng nhất)

### 3.1 "Tổng diện tích" (`total_area_ha`)

**Vấn đề cần quyết định:** tổng diện tích nên là gì?
- (a) Diện tích **quy hoạch/khoanh định** = `SUM(FarmingRegion.area_ha)` - đo năng lực đất đai.
- (b) Diện tích **đang thực canh tác** = `SUM(FarmingPeriod.area_ha)` trong kỳ - đo hoạt động thật.

**Khuyến nghị: dùng (b) làm KPI chính** ("Tổng diện tích đang canh tác"), vì đây mới là
con số phản ánh hoạt động thực tế theo kỳ (khớp với ý nghĩa "so với quý trước" của KPI).
Có thể thêm (a) như 1 thẻ phụ ("Tổng diện tích quy hoạch") nếu cán bộ cần biết còn bao
nhiêu đất trống chưa ai đăng ký canh tác (= (a) - (b)).

**Đồng thời sửa bug:** lọc `FarmingPeriod.created_at` đúng theo `start`/`end` của kỳ (bug
hiện tại ở `get_total_area()` bỏ qua tham số này hoàn toàn - xem mục 1.2).

**Giai đoạn chuyển tiếp:** khi `farming_periods` còn rỗng (mới triển khai, chưa ai khai
báo), KPI này sẽ về 0 - **fallback về `SUM(Farm.area)` như cũ nếu `farming_periods` rỗng**,
để dashboard không đột ngột trống trong lúc dữ liệu thật chưa tích luỹ đủ.

### 3.2 "Tỷ lệ sâu bệnh" (`disease_rate_percent`) - đổi sang tính theo DIỆN TÍCH

**Công thức mới đề xuất:**

```
tỷ lệ sâu bệnh (%) = (tổng area_ha của các FarmingPeriod có >=1 DiseaseDetection
                       trong kỳ) / (tổng area_ha của TẤT CẢ FarmingPeriod trong kỳ) * 100
```

Tức là: trong số diện tích đang canh tác, bao nhiêu % diện tích đó có báo cáo sâu bệnh.
Đây mới đúng nghĩa "tỷ lệ sâu bệnh theo diện tích canh tác" mà tên KPI gợi ý, và khớp với
mô tả trong yêu cầu tính năng này.

Cách tính: `JOIN DiseaseDetection.farming_period_id -> FarmingPeriod`, lấy
`DISTINCT FarmingPeriod.id` có báo cáo bệnh, `SUM(area_ha)` nhóm đó, chia cho
`SUM(area_ha)` toàn bộ `FarmingPeriod` trong kỳ.

**Giới hạn cần biết:** công thức này chỉ tính được cho các ca bệnh có gắn
`farming_period_id`. Ca bệnh không gắn vụ cụ thể (báo cáo cũ, hoặc farmer chưa khai vụ
canh tác) sẽ **không đóng góp vào mẫu số/tử số theo diện tích** - vẫn giữ nguyên cách
tính cũ (đếm theo farm) làm **fallback** khi không đủ dữ liệu `farming_period_id` để
tính theo diện tích (vd < 50% ca bệnh trong kỳ có gắn vụ canh tác thì dùng công thức cũ,
kèm cờ trong response cho FE biết đang dùng công thức nào - tuỳ chọn, không bắt buộc).

### 3.3 Năng suất theo huyện / Xếp hạng huyện

Khuyến nghị dài hạn: nhóm theo `FarmingRegion.district` (qua `FarmingPeriod.region_id`)
thay vì `Farm.location` (text tự do, không kiểm soát được chính tả). Nhưng vì
`YieldPrediction` hiện chỉ có dữ liệu seed gắn với `Farm` (không gắn `FarmingPeriod`),
**việc này phụ thuộc vào việc có nối `YieldPrediction` với `FarmingPeriod` hay không** -
nằm ngoài phạm vi tối thiểu của tài liệu này. Đề xuất: **giữ nguyên nhóm theo
`Farm.location` cho các bảng này ở giai đoạn 1**, chỉ áp dụng thay đổi công thức area-based
cho `disease_rate_percent` (mục 3.2) vì đó là phần được yêu cầu cụ thể.

---

## 4. API cần thêm (chi tiết contract JSON đầy đủ đã có ở `frontend/src/lib/api.ts`)

| Method | Path | Việc cần làm |
|---|---|---|
| `POST` | `/farming-regions` | Cán bộ tạo vùng canh tác. Body: `{name, district, areaHa}`. Trả về bản ghi vừa tạo. |
| `GET` | `/farming-regions` | Trả `{regions: [...]}` - toàn bộ danh sách. |
| `POST` | `/farming-periods` | Nông dân khai vụ canh tác. Body: `{regionId, cropType, areaHa, cropCount}`. Nên validate `areaHa` vụ này không vượt quá `areaHa` còn trống của region (tổng các period hiện có trong region đó cộng thêm không vượt `region.area_ha`) - trả lỗi 400 nếu vượt, kèm thông báo tiếng Việt rõ ràng. Trả về bản ghi vừa tạo kèm `regionName` (join sẵn). |
| `GET` | `/farming-periods` | Trả `{periods: [...]}` kèm `regionName` đã join. |

Không cần userId/token cho các endpoint trên - app hiện không có đăng nhập thật (chỉ có
màn chọn vai trò ở trang chủ), giống cách `/disease-report` đang hoạt động.

### 4.1 Sửa nhỏ ở endpoint có sẵn

`POST /disease/detect` (file `frontend_disease.py`): thêm 1 field `Form` tuỳ chọn:

```python
farmingPeriodId: Optional[int] = Form(None)
```

và lưu vào `DiseaseDetection.farming_period_id` nếu có. Frontend hiện **chưa gửi** field
này (trang /scan chưa có UI chọn vụ canh tác khi báo cáo bệnh) - đây là việc CẦN làm ở
frontend trong 1 lượt sau nếu muốn công thức area-based ở mục 3.2 có đủ dữ liệu. Backend
cứ thêm field optional trước, không phá tương thích ngược.

---

## 5. Rollout / migration

- Dùng cơ chế `Base.metadata.create_all()` sẵn có ở `main.py` - 2 bảng mới + 1 cột mới
  trên `disease_detections` sẽ tự tạo khi restart backend, **không cần Alembic** (đúng
  quy ước MVP hiện tại của dự án).
- **Lưu ý:** `create_all()` chỉ tạo bảng CHƯA TỒN TẠI, **không tự thêm cột mới vào bảng
  đã tồn tại** (`disease_detections` đã có sẵn trong `dienbien_agri.db`). Cột
  `farming_period_id` mới thêm vào model sẽ **không tự xuất hiện** trong file DB hiện
  tại - cần 1 trong 2 cách:
  1. Xoá file `dienbien_agri.db` để `create_all()` tạo lại từ đầu (mất dữ liệu demo hiện
     có, chấp nhận được nếu chưa lên production), hoặc
  2. Chạy `ALTER TABLE disease_detections ADD COLUMN farming_period_id INTEGER` thủ công
     1 lần trước khi restart (giữ dữ liệu cũ).
- Không cần backfill `farming_period_id` cho dữ liệu `disease_detections` cũ - để NULL,
  đã tính đến ở công thức fallback (mục 3.2).
- Không cần seed dữ liệu mẫu cho `farming_regions`/`farming_periods` - để trống, 2 trang
  quản lý mới sẽ tự hiển thị trạng thái rỗng đúng như đã build ở frontend.

---

## 6. Việc KHÔNG làm (giữ phạm vi thay đổi tối thiểu)

- Không sửa bảng `Farm`, `User`, `YieldPrediction` hiện có.
- Không thêm hệ thống đăng nhập/phân quyền.
- Không migrate `Farm.location`/`DiseaseDetection.district` sang tham chiếu
  `FarmingRegion` - 2 hệ thống (cũ: text tự do, mới: FK có cấu trúc) tồn tại song song,
  không ép buộc thống nhất ngay.
- Không đổi nhóm theo huyện ở `districtYield`/`districtRankings` (mục 3.3) - để giai đoạn sau.
- Không xoá `app/services/dashboard_service.py` (dead code) trong lần này - chỉ ghi chú
  lại để tránh sửa nhầm chỗ không dùng tới.
