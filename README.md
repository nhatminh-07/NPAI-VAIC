# AI Nông Nghiệp Điện Biên

> ⚠️ **Đây là bản DEMO/MVP**, được xây dựng để trình diễn ý tưởng sản phẩm. Dữ liệu (giá nông sản, lịch sử năng suất, tình hình dịch bệnh...) là dữ liệu mẫu/mô phỏng, mô hình AI là mô hình rút gọn dùng cho minh họa. **Không dùng kết quả của hệ thống này để ra quyết định canh tác hay giao dịch thực tế.**

Hệ thống AI hỗ trợ nông nghiệp thông minh cho tỉnh Điện Biên, gồm 2 luồng trải nghiệm riêng biệt: **Nông dân** (chẩn đoán bệnh, dự báo năng suất, xem giá) và **Cán bộ nông nghiệp** (dashboard tổng hợp toàn tỉnh).

## Mục lục

- [Tính năng chính](#tính-năng-chính)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Cách chạy](#cách-chạy)
- [API Endpoints](#api-endpoints)
- [Deploy](#deploy)
- [Môi trường](#môi-trường)
- [Giới hạn của bản demo](#giới-hạn-của-bản-demo)

## Tính năng chính

### 🧑‍🌾 Giao diện Nông dân (`/scan`, `/forecast`, `/prices`)

1. **Chẩn đoán bệnh cây trồng qua ảnh** (`/scan`)
   - Chụp/tải ảnh lá, thân cây trực tiếp trên điện thoại.
   - AI xác định bệnh (đạo ôn lúa, bạc lá vi khuẩn, gỉ sắt cà phê, sâu đục quả cà phê, sương mai rau màu, rệp hại rau màu...) kèm mức độ tin cậy.
   - Hệ thống dựa trên đặc điểm hình thái vết bệnh đặc trưng của từng loại bệnh (màu sắc, hình dạng, vị trí phân bố trên lá) — đây là phương pháp chẩn đoán truyền thống mà các chuyên gia nông nghiệp/bệnh học thực vật vẫn sử dụng ngoài thực địa. Hệ thống được thích ứng và phát triển
   - Hiển thị mức độ nghiêm trọng (nhẹ/trung bình/nặng) và cảnh báo khi độ tin cậy thấp, yêu cầu chụp lại ảnh rõ hơn.
   - Đưa ra khuyến nghị xử lý (cách ly cây bệnh, phun thuốc, theo dõi độ ẩm...).
   - Lưu lại báo cáo chẩn đoán theo từng nông trại (farm).

2. **Dự báo năng suất & thời điểm thu hoạch** (`/forecast`)
   - Nhập thông tin vụ mùa: loại cây trồng (lúa/cà phê/rau màu), diện tích, ngày gieo trồng, huyện/thị xã.
   - Mô hình LightGBM dự đoán năng suất (tấn/ha), tổng sản lượng dự kiến, thời điểm thu hoạch tối ưu.
   - Hiển thị độ tin cậy, mức độ rủi ro (thấp/trung bình/cao) và cơ sở dự báo.

3. **Giá thị trường nông sản** (`/prices`)
   - Xem giá hiện tại và mức thay đổi trong 7 ngày gần nhất.
   - Biểu đồ lịch sử giá kết hợp dự báo xu hướng giá (mô hình Holt-Winters) kèm khoảng tin cậy.
   - Khuyến cáo thông tin chỉ mang tính tham khảo, không phải khuyến nghị mua/bán.

### 🏢 Giao diện Cán bộ nông nghiệp (`/dashboard`)

4. **Dashboard so sánh tổng hợp toàn tỉnh**
   - So sánh năng suất, sản lượng, tỷ lệ ca bệnh theo quý/năm (so với kỳ trước, so với cùng kỳ năm trước).
   - Lọc theo kỳ báo cáo và loại cây trồng.
   - Biểu đồ năng suất theo huyện, biểu đồ số ca bệnh theo loại, biểu đồ xu hướng dịch bệnh theo quý.
   - Bảng xếp hạng huyện theo năng suất, sản lượng, số ca bệnh (có thể sắp xếp theo cột).

### 🔧 Tính năng backend bổ sung (chưa có giao diện riêng, đã sẵn sàng API)

5. **Đề xuất cây trồng phù hợp** (`/crop/recommend`) — gợi ý loại cây trồng dựa trên thông số đất (N, P, K, pH) và khí hậu (nhiệt độ, độ ẩm, lượng mưa).
6. **Thời tiết khu vực** (`/weather/current`, `/weather/forecast`) — thời tiết hiện tại và dự báo 7 ngày cho khu vực Điện Biên.

### 🎛️ Trải nghiệm chung

- Màn hình chọn vai trò (Nông dân / Cán bộ) khi mở ứng dụng.
- Giao diện tối ưu cho thiết bị di động, chuyển trang mượt (page transition).
- Trạng thái tải (skeleton loading), trạng thái rỗng, trạng thái lỗi khi không kết nối được máy chủ.

## Công nghệ sử dụng

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM (hỗ trợ SQLite/PostgreSQL)
- **LightGBM / scikit-learn** - Dự báo năng suất, đề xuất cây trồng
- **Statsmodels (Holt-Winters)** - Dự báo giá thị trường
- **Pillow / NumPy / Pandas** - Xử lý ảnh và dữ liệu

### Frontend
- **Next.js 15** - React framework (App Router)
- **React 19** & **TypeScript** - UI & type safety
- **TailwindCSS** - Styling
- **Recharts** - Biểu đồ và visualization

## Cấu trúc thư mục

```
NPAI-VAIC/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # Entrypoint
│   │   ├── config.py       # Cấu hình
│   │   ├── database.py     # Database connection
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── routers/        # API endpoints (disease, yield, price, dashboard, crop, weather...)
│   │   ├── services/       # Business logic & mô hình dự báo/đề xuất
│   │   └── ml/             # ML models & dữ liệu huấn luyện
│   ├── seed_data.py        # Seed dữ liệu mẫu
│   └── requirements.txt
│
└── frontend/                 # Next.js Frontend
    ├── src/app/
    │   ├── (farmer)/        # Luồng nông dân: scan, forecast, prices
    │   └── (officer)/       # Luồng cán bộ: dashboard
    ├── src/components/      # React components (UI & layout)
    ├── src/constants/       # Copy tiếng Việt, danh sách cây trồng/huyện
    ├── src/lib/             # Utilities & API client
    └── public/              # Static assets
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

# Seed dữ liệu mẫu
python seed_data.py

# Chạy server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend

# Cài dependencies
npm install

# Chạy development server
npm run dev
```

Mở: **http://localhost:3000**

## API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/detect-disease` | POST | Nhận diện sâu bệnh từ ảnh (API gốc, có lưu DB) |
| `/predict-yield` | POST | Dự báo năng suất (API gốc, có lưu DB) |
| `/market-price` | GET | Lấy giá thị trường (API gốc) |
| `/detect` | POST | Nhận diện sâu bệnh (API cho frontend) |
| `/predict` | POST | Dự báo năng suất (API cho frontend) |
| `/price` | GET | Giá thị trường (API cho frontend) |
| `/dashboard` | GET | Dashboard so sánh kỳ |
| `/crop/recommend` | POST | Đề xuất cây trồng theo thông số đất/khí hậu |
| `/weather/current` | GET | Thời tiết hiện tại |
| `/weather/forecast` | GET | Dự báo thời tiết 7 ngày |

## Deploy

### Backend (Render)

1. Connect GitHub repo với Render
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Thêm `DATABASE_URL` environment variable

### Frontend (Vercel)

1. Connect GitHub repo với Vercel
2. Root Directory: `frontend`
3. Build Command: `npm run build`
4. Output Directory: `.next`

## Môi trường

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:<password>@<host>:5432/postgres
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Giới hạn của bản demo

- Đây là **MVP phục vụ mục đích trình diễn**, chưa phải sản phẩm hoàn chỉnh cho môi trường production.
- Mô hình nhận diện bệnh cây dùng mô hình rút gọn; các thư viện deep learning đầy đủ (`transformers`, `torch`, `torchvision`) đang được **để tắt** trong `requirements.txt` để tránh lỗi khi chạy demo trên Windows.
- Dữ liệu giá thị trường, lịch sử năng suất, số liệu dashboard là **dữ liệu mẫu** (seed data), chưa kết nối nguồn dữ liệu thật của tỉnh.
- Ảnh chẩn đoán bệnh hiện lưu cục bộ trên máy chủ (`uploaded_images/`); môi trường production nên chuyển sang dịch vụ lưu trữ đối tượng (Supabase Storage/CDN...).
- Tính năng đề xuất cây trồng và thời tiết đã có API backend nhưng **chưa có giao diện người dùng** tương ứng.
- Bản đồ nhiệt (heatmap) vùng bệnh trên ảnh chẩn đoán dự kiến bổ sung ở phiên bản tiếp theo.