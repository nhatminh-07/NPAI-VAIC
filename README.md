# Hệ thống quản lí nông sản Gạo Bản

> *"Đồng hành để vươn xa"*


**Gạo Bản** là hệ thống AI hỗ trợ nông nghiệp thông minh cho tỉnh Điện Biên, gồm 2 luồng trải nghiệm riêng biệt theo vai trò: **Nông dân** (chẩn đoán bệnh, dự báo năng suất, xem giá, khai báo vụ canh tác) và **Cán bộ nông nghiệp** (dashboard tổng hợp toàn tỉnh, quản lý vùng canh tác, theo dõi báo cáo sâu bệnh). Một **trợ lý AI** (chatbot) đồng hành trên mọi màn hình.

## 🔗 Bản triển khai trực tuyến (Live demo)

| Thành phần | Link |
|-----------|------|
| **Frontend** (Vercel) | https://agriplatform-neon.vercel.app/dashboard |
| **Backend API + Swagger docs** (Render) | https://npai-vaic.onrender.com/docs |

> Backend chạy trên gói miễn phí của Render nên **lần gọi đầu tiên có thể mất 30–60 giây để "đánh thức" máy chủ** (cold start). Nếu dashboard hiển thị trạng thái lỗi/rỗng, hãy chờ và bấm "Thử lại".

## Mục lục

- [Tính năng chính](#tính-năng-chính)
- [Kiến trúc & mô hình dữ liệu](#kiến-trúc--mô-hình-dữ-liệu)
- [Kịch bản demo cho ban giám khảo](#kịch-bản-demo-cho-ban-giám-khảo)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cách chạy](#cách-chạy)
- [API Endpoints](#api-endpoints)
- [Deploy](#deploy)
- [Môi trường](#môi-trường)
- [Giới hạn của bản demo](#giới-hạn-của-bản-demo)

## Tính năng chính

### 🧑‍🌾 Giao diện Nông dân (`/scan`, `/forecast`, `/prices`, `/farming-periods`)

1. **Chẩn đoán bệnh cây trồng qua ảnh** (`/scan`)
   - Chụp/tải ảnh lá, thân cây trực tiếp trên điện thoại (hỗ trợ kéo-thả và camera).
   - Nhập kèm **loại cây trồng**, **số cây bị bệnh** và (tùy chọn) **vùng canh tác** nơi phát hiện bệnh.
   - AI xác định bệnh (đạo ôn lúa, bạc lá vi khuẩn, gỉ sắt cà phê, sâu đục quả cà phê, sương mai rau màu, rệp hại rau màu...) kèm mức độ tin cậy.
   - Hệ thống dựa trên đặc điểm hình thái vết bệnh đặc trưng của từng loại bệnh (màu sắc, hình dạng, vị trí phân bố trên lá) — đây là phương pháp chẩn đoán truyền thống mà các chuyên gia nông nghiệp/bệnh học thực vật vẫn sử dụng ngoài thực địa. Hệ thống được thích ứng và phát triển
   - Hiển thị mức độ nghiêm trọng (khỏe/nhẹ/trung bình/nặng) và cảnh báo khi độ tin cậy < 60%, yêu cầu chụp lại ảnh rõ hơn.
   - Đưa ra khuyến nghị xử lý (cách ly cây bệnh, phun thuốc, theo dõi độ ẩm...) dạng checklist tương tác.
   - Mỗi lượt chẩn đoán được **lưu lại làm một báo cáo sâu bệnh**, gắn với vùng canh tác nếu có → hiện lên dashboard & trang báo cáo của cán bộ.

2. **Dự báo năng suất & thời điểm thu hoạch** (`/forecast`)
   - Nhập thông tin vụ mùa: loại cây trồng (lúa/cà phê/rau màu), diện tích, ngày gieo trồng, huyện/thị xã.
   - Mô hình ML (LightGBM/scikit-learn) đối chiếu với điều kiện thời tiết thực tế (Open-Meteo) và đặc điểm sinh trưởng của cây để dự đoán năng suất (tấn/ha), tổng sản lượng dự kiến, khoảng thời gian thu hoạch tối ưu.
   - Hiển thị độ tin cậy, mức độ rủi ro (thấp/trung bình/cao) và cơ sở dự báo.

3. **Giá thị trường nông sản** (`/prices`)
   - Xem giá hiện tại và mức thay đổi trong 7 ngày gần nhất theo từng loại cây.
   - Biểu đồ lịch sử giá kết hợp dự báo xu hướng giá (mô hình Holt-Winters) kèm khoảng tin cậy.
   - Khuyến cáo thông tin chỉ mang tính tham khảo, không phải khuyến nghị mua/bán.

4. **Quản lý vụ canh tác** (`/farming-periods`)
   - Khai báo một **vụ canh tác** (loại cây, diện tích, số lượng cây) trong một **vùng canh tác** do cán bộ đã tạo sẵn.
   - Xem và **xóa** các vụ canh tác đã khai báo.
   - Dữ liệu vụ canh tác trực tiếp cấp số liệu cho dashboard của cán bộ (diện tích canh tác, năng suất trung bình theo huyện).

### 🏢 Giao diện Cán bộ nông nghiệp (`/dashboard`, `/disease-report`, `/management`)

5. **Dashboard so sánh tổng hợp toàn tỉnh** (`/dashboard`)
   - 4 chỉ số KPI: **tổng diện tích canh tác**, **năng suất trung bình (tấn/ha)**, **số ca sâu bệnh**, **tỷ lệ sâu bệnh (%)** — kèm % thay đổi so với kỳ trước.
   - Lọc theo **kỳ báo cáo (quý)** và **loại cây trồng**.
   - Biểu đồ năng suất theo huyện (kỳ hiện tại vs kỳ trước), số ca bệnh theo loại, xu hướng dịch bệnh 4 quý gần nhất.
   - Bảng xếp hạng huyện theo năng suất/sản lượng/số ca bệnh (sắp xếp theo cột).
   - **Toàn bộ số liệu dashboard được tính theo kỳ và lấy trực tiếp từ hệ thống quản lý vùng/vụ canh tác** (xem [Kiến trúc & mô hình dữ liệu](#kiến-trúc--mô-hình-dữ-liệu)).

6. **Báo cáo sâu bệnh** (`/disease-report`)
   - Danh sách toàn bộ báo cáo chẩn đoán bệnh của nông dân (huyện, loại cây, tên bệnh, mức độ, số cây bị bệnh, ngày báo cáo).

7. **Quản lý vùng canh tác** (`/management`)
   - Tạo **vùng canh tác** (tên, huyện thuộc Điện Biên, diện tích ha) — đây là "hạ tầng" mà nông dân chọn khi khai báo vụ canh tác.
   - Xem và **xóa** vùng canh tác (xóa vùng sẽ xóa các vụ canh tác thuộc vùng, đồng thời gỡ liên kết vùng khỏi các báo cáo sâu bệnh nhưng vẫn giữ lại bản ghi báo cáo).

### 🤖 Trợ lý AI (chatbot)

8. **Trợ lý AI** (`/assistant/chat`) — bong bóng chat nổi trên mọi trang, bật/tắt được như widget hỗ trợ khách hàng. Người dùng có thể hỏi bằng tiếng Việt (vd *"Tóm tắt những sự kiện trong quý 3 năm 2025"*); backend tổng hợp dữ liệu và trả lời. Kèm các câu gợi ý nhanh khi mở khung chat.

### 🎛️ Trải nghiệm chung

- **Màn hình chọn vai trò** (Nông dân / Cán bộ) khi mở ứng dụng — không có đăng nhập, chỉ điều hướng theo vai trò.
- **Chủ đề "xanh sinh thái"** thống nhất, logo Gạo Bản, font **Be Vietnam Pro** (hiển thị tốt dấu tiếng Việt).
- Giao diện **mobile-first cho nông dân** (thanh điều hướng dưới, chuyển trang có hiệu ứng trượt) và **desktop sidebar cho cán bộ**.
- Trạng thái tải (skeleton loading), trạng thái rỗng, trạng thái lỗi/mất kết nối máy chủ có nút "Thử lại" — nhất quán trên toàn ứng dụng.

## Kiến trúc & mô hình dữ liệu

Điểm cốt lõi trong thiết kế: **mọi hoạt động đều liên kết với nhau và được neo theo KỲ (quý)**, để dashboard của cán bộ phản ánh đúng hoạt động thực tế của nông dân theo từng kỳ báo cáo — không có hai "nguồn sự thật" tách rời.

**Ba bảng trung tâm** (SQLAlchemy, xem `backend/app/models.py`):

| Bảng | Ai tạo | Trường chính | Vai trò |
|------|--------|--------------|---------|
| `FarmingRegion` (vùng canh tác) | Cán bộ | `name`, `district`, `area_ha`, `created_at` | Khu vực canh tác thuộc 1 huyện. Là đơn vị gốc để tính "tổng diện tích". |
| `FarmingPeriod` (vụ canh tác) | Nông dân | `region_id`, `crop_type`, `area_ha`, `crop_count`, `created_at` | 1 vụ mùa trong 1 vùng. Cấp dữ liệu năng suất & mật độ trồng. |
| `DiseaseDetection` (báo cáo bệnh) | Nông dân | `crop_type`, `severity`, `affected_plant_count`, `farming_region_id`, `created_at` | Mỗi lượt chẩn đoán = 1 bản ghi, gắn (tùy chọn) với vùng canh tác. |

**Cách dashboard tính KPI (theo kỳ đang chọn, dựa trên `created_at`):**

- **Tổng diện tích** = tổng `area_ha` của tất cả vùng canh tác *được tạo trong kỳ đó*.
- **Năng suất trung bình** = năng suất cơ sở theo loại cây, **điều chỉnh theo mật độ trồng thực tế** (`crop_count / area_ha` mà nông dân khai) — trồng dày hơn → năng suất/ha cao hơn (giới hạn 0.6×–1.4×), rồi lấy trung bình có trọng số theo diện tích các vụ.
- **Số ca sâu bệnh** = số báo cáo bệnh trong kỳ.
- **Tỷ lệ sâu bệnh** = tổng diện tích các vùng *có ≥1 báo cáo bệnh* / tổng diện tích tất cả vùng trong kỳ (tính **theo diện tích**, không phải đếm số nông trại).
- Biểu đồ/bảng theo huyện được nhóm theo `FarmingRegion.district` (dùng đúng chuẩn tên huyện của frontend, không tiền tố "Huyện").

Nhờ neo theo `created_at`: dữ liệu cán bộ/nông dân nhập **trong lúc demo** có mốc thời gian = hiện tại = quý hiện tại, nên **hiện lên dashboard quý hiện tại ngay lập tức**.

## Kịch bản demo cho ban giám khảo

Dữ liệu mẫu (`seed_data.py`) được thiết kế riêng cho demo:

1. **Ba quý trước** (Q4/2025, Q1/2026, Q2/2026) đã có sẵn dữ liệu **khác nhau** (số vùng, diện tích, năng suất, số ca bệnh khác biệt rõ giữa các kỳ) — chuyển bộ lọc "Kỳ báo cáo" để thấy mỗi quý một bức tranh riêng.
2. **Quý hiện tại được để TRỐNG có chủ đích** — mở dashboard mặc định sẽ thấy các KPI = 0 và biểu đồ ở trạng thái rỗng.
3. **Lấp đầy quý hiện tại ngay trên sân khấu:**
   - Vào vai **Cán bộ** → `/management` → tạo một vùng canh tác → quay lại dashboard: "Tổng diện tích" tăng lên ngay.
   - Vào vai **Nông dân** → `/farming-periods` → khai một vụ canh tác trong vùng đó → dashboard có thêm năng suất theo huyện.
   - Vào vai **Nông dân** → `/scan` → chẩn đoán một ảnh bệnh, chọn vùng canh tác → "Số ca / Tỷ lệ sâu bệnh" cập nhật.
   - Thử **xóa** vùng/vụ canh tác để thấy dashboard trở lại như cũ.

## Công nghệ sử dụng

### Backend
- **FastAPI** - API framework (Swagger docs tự sinh tại `/docs`)
- **SQLAlchemy** - ORM (SQLite cho local/demo, hỗ trợ PostgreSQL cho production)
- **LightGBM / scikit-learn** - Dự báo năng suất
- **Statsmodels (Holt-Winters)** - Dự báo giá thị trường
- **Open-Meteo API** - Dữ liệu thời tiết thực tế cho dự báo năng suất
- **Pillow / NumPy / Pandas** - Xử lý ảnh và dữ liệu

### Frontend
- **Next.js 15** - React framework (App Router, route groups `(farmer)` / `(officer)`)
- **React 19** & **TypeScript** - UI & type safety (mọi lời gọi backend tập trung ở `src/lib/api.ts`)
- **TailwindCSS** - Styling (chủ đề xanh sinh thái)
- **Recharts** - Biểu đồ và visualization
- **next/font** - Font Be Vietnam Pro (subset tiếng Việt)

## Cấu trúc thư mục

```
NPAI-VAIC/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # Entrypoint + đăng ký router + create_all
│   │   ├── config.py                # Cấu hình (DATABASE_URL, CORS, đường dẫn ML...)
│   │   ├── database.py              # Kết nối DB & session
│   │   ├── models.py                # SQLAlchemy models (Farm, FarmingRegion, FarmingPeriod, DiseaseDetection...)
│   │   ├── schemas.py               # Pydantic schemas
│   │   ├── routers/                 # API endpoints
│   │   │   ├── frontend_disease.py  #   /disease/detect, /disease-report
│   │   │   ├── frontend_yield.py    #   /yield/predict
│   │   │   ├── frontend_market.py   #   /market/price
│   │   │   ├── frontend_dashboard.py#   /dashboard (region-centric, theo kỳ)
│   │   │   ├── frontend_farming.py  #   /farming-regions, /farming-periods (+ DELETE)
│   │   │   ├── assistant.py         #   /assistant/chat (trợ lý AI)
│   │   │   └── disease.py, yield_forecast.py, market_price.py  # API gốc
│   │   ├── services/                # Business logic & mô hình dự báo/đề xuất
│   │   └── ml/                      # ML models & dữ liệu huấn luyện
│   ├── seed_data.py                 # Seed dữ liệu mẫu (3 quý trước có dữ liệu, quý hiện tại để trống)
│   ├── REQUIREMENTS_farming_management.md  # Tài liệu thiết kế tính năng quản lý vùng/vụ canh tác
│   └── requirements.txt
│
└── frontend/                         # Next.js Frontend
    ├── src/app/
    │   ├── page.tsx                 # Màn chọn vai trò
    │   ├── (farmer)/                # Luồng nông dân: scan, forecast, prices, farming-periods
    │   └── (officer)/               # Luồng cán bộ: dashboard, disease-report, management
    ├── src/components/
    │   ├── ui/                      # Button, Card, Select, Badge, Logo, Spinner...
    │   ├── layout/                  # FarmerShell, OfficerShell, PageTransition
    │   └── chat/                    # ChatWidget (trợ lý AI)
    ├── src/constants/               # copy.ts (toàn bộ chữ tiếng Việt), crops, districts, periods
    ├── src/lib/api.ts               # Client API duy nhất (mọi lời gọi backend)
    ├── src/types/api.ts             # Kiểu dữ liệu contract FE↔BE
    └── public/                      # Static assets (logo, icon)
```

## Cách chạy

### Backend

```bash
cd backend

# Tạo virtual environment (PHẢI DÙNG PYTHON CÓ VER =< 12)
python -m venv venv
source venv/Scripts/activate  # Linux/Mac
# hoặc
.\venv\Scripts\activate  # Windows

# Cài dependencies
pip install -r requirements.txt

# Seed dữ liệu mẫu (tạo dữ liệu 3 quý trước, để trống quý hiện tại cho demo)
python seed_data.py

# Chạy server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs (Swagger UI): **http://localhost:8000/docs**

### Frontend

```bash
cd frontend

# Cài dependencies
npm install

# Chạy development server
npm run dev
```

Mở: **http://localhost:3000**

> Frontend đọc địa chỉ backend từ `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`) — xem [Môi trường](#môi-trường).

## API Endpoints

Danh sách các endpoint đang được đăng ký (xác thực từ `/openapi.json`):

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/` | GET | Health check |
| `/dashboard` | GET | Dashboard so sánh kỳ (KPI, biểu đồ, xếp hạng huyện) — tham số `period`, `cropId` |
| `/disease/detect` | POST | Chẩn đoán bệnh từ ảnh (multipart: `image`, `cropType`, `affectedPlantCount`, `regionId?`) + lưu báo cáo |
| `/disease-report` | GET | Danh sách báo cáo sâu bệnh (cho trang cán bộ) |
| `/farming-regions` | GET, POST | Danh sách / tạo vùng canh tác |
| `/farming-regions/{id}` | DELETE | Xóa vùng canh tác (cascade vụ canh tác, gỡ liên kết báo cáo bệnh) |
| `/farming-periods` | GET, POST | Danh sách / khai báo vụ canh tác (kèm kiểm tra diện tích không vượt quá vùng) |
| `/farming-periods/{id}` | DELETE | Xóa vụ canh tác |
| `/yield/predict` | POST | Dự báo năng suất & thời điểm thu hoạch |
| `/market/price` | GET | Giá thị trường (lịch sử + dự báo) theo `cropId` |
| `/assistant/chat` | POST | Trợ lý AI (body: `message`, `history`) |
| `/detect-disease` | POST | Nhận diện sâu bệnh — **API gốc** (giữ lại để tương thích) |
| `/predict-yield` | POST | Dự báo năng suất — **API gốc** |
| `/market-price` | GET | Giá thị trường — **API gốc** |
| `/admin/seed` | POST | Seed lại dữ liệu mẫu (chỉ dùng khi setup) |

> Ghi chú: mã nguồn còn có service cho **đề xuất cây trồng** và **thời tiết** (`app/services/`) nhưng router tương ứng **hiện chưa được đăng ký** trong `main.py`, nên chưa xuất hiện trong API đang chạy — thuộc phần mở rộng cho phiên bản sau.

## Deploy

### Backend (Render)

1. Connect GitHub repo với Render
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Thêm `DATABASE_URL` environment variable (và `CORS_ORIGINS` trỏ tới domain Vercel)
5. Đang chạy tại: **https://npai-vaic.onrender.com/docs**

### Frontend (Vercel)

1. Connect GitHub repo với Vercel
2. Root Directory: `frontend`
3. Build Command: `npm run build`
4. Output Directory: `.next`
5. Thêm `NEXT_PUBLIC_API_URL` = URL backend trên Render
6. Đang chạy tại: **https://agriplatform-neon.vercel.app**

## Môi trường
### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:<password>@<host>:5432/postgres
CORS_ORIGINS=http://localhost:3000,https://agriplatform-neon.vercel.app
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

