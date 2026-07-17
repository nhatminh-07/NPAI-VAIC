# AI Nông Nghiệp Điện Biên — Backend MVP (48h)

Backend monolith FastAPI hiện thực đúng 4 chức năng đã thiết kế:
1. Nhận diện sâu bệnh (`POST /detect-disease`)
2. Dự báo năng suất & thời điểm thu hoạch (`POST /predict-yield`)
3. Phân tích giá thị trường (`GET /market-price`)
4. Dashboard so sánh kỳ (`GET /dashboard`)

## Khác biệt so với thiết kế gốc (đã kiểm chứng bằng cách chạy thật)

| Thành phần | Thiết kế gốc | Đã dùng trong code | Vì sao |
|---|---|---|---|
| Database | Supabase PostgreSQL | **SQLite** (local file) qua SQLAlchemy | Chạy được ngay, không cần tạo project Supabase để demo/dev. Đổi sang Postgres chỉ cần sửa 1 biến `DATABASE_URL` (xem bên dưới) — code không cần sửa gì thêm vì dùng SQLAlchemy ORM. |
| Storage ảnh | Supabase Storage | **Lưu file local** ở `backend/uploaded_images/`, phục vụ qua `/static/uploaded_images/...` | Tương tự — tránh phụ thuộc dịch vụ ngoài khi demo. Đổi sang Supabase Storage chỉ cần sửa hàm lưu file trong `app/routers/disease.py`. |
| Dự báo giá | Prophet | **Holt-Winters (statsmodels)** | Prophet cần build backend Stan (C++), rất dễ lỗi cài đặt (đã tự kiểm chứng: bị chặn tải CmdStan trong môi trường sandbox). Holt-Winters cho kết quả xu hướng + mùa vụ tương đương, chạy ổn định, không cần compiler. Nếu máy bạn cài Prophet được, có thể thay thế trong `app/services/price_service.py` mà không đổi API. |
| Nhận diện sâu bệnh | YOLOv8 (train/fine-tune) | **Heuristic phân loại theo màu sắc ảnh** (demo) | Không đủ thời gian/dataset gán nhãn thật trong 48h để train YOLOv8 cho cây trồng Điện Biên. Code đã được viết theo kiến trúc pipeline giống thật (ảnh → model → nhãn + confidence → gợi ý xử lý → lưu DB) để khi có model YOLOv8 thật, chỉ cần thay 1 hàm `_classify_image()` trong `app/services/disease_service.py` (đã có hướng dẫn chi tiết ngay trong comment của file). **Cần nói rõ điều này với ban giám khảo khi demo.** |

Toàn bộ các API đã được chạy thử thành công (health check, predict-yield, market-price, dashboard) trước khi gửi cho bạn.

## Cấu trúc thư mục

```
backend/
  app/
    main.py                 # Entrypoint FastAPI, gắn router + CORS + static files
    config.py                # Đường dẫn, DATABASE_URL, ...
    database.py              # SQLAlchemy engine/session
    models.py                 # ORM: Users, Farms, Crops, DiseaseDetections,
                               # YieldPredictions, WeatherHistory, MarketPrice, Reports
    schemas.py                 # Pydantic request/response
    routers/
      disease.py               # POST /detect-disease
      yield_forecast.py         # POST /predict-yield
      market_price.py           # GET /market-price
      dashboard.py               # GET /dashboard
    services/
      disease_service.py        # Logic nhận diện sâu bệnh (demo heuristic)
      yield_service.py           # Logic dự báo năng suất (LightGBM)
      price_service.py           # Logic phân tích giá (Holt-Winters)
      dashboard_service.py        # Logic so sánh kỳ hiện tại/kỳ trước
    ml/
      generate_sample_data.py     # Sinh dữ liệu mẫu (năng suất, giá)
      train_yield_model.py         # Train + lưu model LightGBM
      yield_model.joblib            # Model đã train sẵn (đi kèm)
    data/
      sample_yield_history.csv      # Dữ liệu mẫu năng suất (đi kèm)
      sample_prices.csv               # Dữ liệu mẫu giá (đi kèm)
      disease_recommendations.json     # Bảng tra gợi ý xử lý theo bệnh
  seed_data.py                # Seed Users/Farms/Crops + lịch sử demo cho dashboard
  requirements.txt
```

## Cách chạy (local)

```bash
cd backend
venv\Scripts\activate.bat      #dùng cmd
python3 -m venv venv

pip install -r requirements.txt

# 1. (Đã có sẵn file .csv/.joblib mẫu, nhưng nếu muốn sinh lại/train lại từ đầu:)
python -m app.ml.generate_sample_data
python -m app.ml.train_yield_model

# 2. Seed dữ liệu mẫu vào DB (users, farms, lịch sử phát hiện/dự báo) để dashboard có số liệu
python seed_data.py

# 3. Chạy server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt: **http://localhost:8000/docs** — Swagger UI để test trực tiếp cả 4 API, không cần Postman.

## Test nhanh bằng curl

```bash
# Dự báo năng suất
curl -X POST http://localhost:8000/predict-yield \
  -H "Content-Type: application/json" \
  -d '{"crop_name":"rice","area_ha":2.5,"sowing_date":"2026-01-10"}'

# Phân tích giá cà phê, dự báo 7 ngày tới
curl "http://localhost:8000/market-price?crop_name=coffee&forecast_days=7"

# Dashboard so sánh quý hiện tại vs quý trước
curl "http://localhost:8000/dashboard?period=quarter"

# Nhận diện sâu bệnh (thay path ảnh thật)
curl -X POST http://localhost:8000/detect-disease \
  -F "image=@/duong/dan/anh_la_cay.jpg" \
  -F "crop_name=rice"
```

`crop_name` hợp lệ: `rice`, `coffee`, `vegetable` (khớp với dữ liệu mẫu đã sinh).

## Đổi sang Supabase Postgres khi cần triển khai thật

1. Tạo project trên supabase.com, lấy connection string Postgres.
2. Đặt biến môi trường trước khi chạy:
   ```bash
   export DATABASE_URL="postgresql://postgres:<password>@<host>:5432/postgres"
   ```
3. Không cần sửa code — `app/config.py` tự đọc từ `DATABASE_URL`, SQLAlchemy tự tạo bảng qua `Base.metadata.create_all()`.
4. Với ảnh upload: sửa `app/routers/disease.py` để dùng Supabase Storage SDK thay vì lưu file local (hiện đang lưu vào `backend/uploaded_images/`).

## Deploy nhanh cho demo (gợi ý)

- **Backend**: Render.com (free tier) — connect repo, set start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, thêm biến `DATABASE_URL` nếu dùng Supabase.
- **Frontend**: chưa có trong bản này (tài liệu gốc dùng React + Vite + Tailwind). Nếu cần, tôi có thể sinh tiếp phần frontend gọi 4 API này — chỉ cần bạn xác nhận.

## Việc cần làm tiếp nếu còn thời gian trong 48h

1. Thay heuristic nhận diện sâu bệnh bằng YOLOv8 thật nếu có dataset ảnh (dù chỉ vài trăm ảnh/loại bệnh cũng cải thiện đáng kể so với demo).
2. Nối dữ liệu giá/thời tiết thật (API hoặc dữ liệu tỉnh cung cấp) thay cho `sample_prices.csv` / weather mẫu trong `yield_service.py`.
3. Dựng frontend React theo đúng sơ đồ kiến trúc để demo trực quan trước ban giám khảo.
