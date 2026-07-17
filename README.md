# AI Nông Nghiệp Điện Biên

Hệ thống AI hỗ trợ nông nghiệp thông minh cho tỉnh Điện Biên.

## Các tính năng chính

1. **Nhận diện sâu bệnh** - Upload ảnh lá/thân cây để AI xác định bệnh và đề xuất biện pháp xử lý
2. **Dự báo năng suất** - Dự đoán sản lượng và thời điểm thu hoạch tối ưu
3. **Phân tích giá thị trường** - Theo dõi và dự báo xu hướng giá nông sản
4. **Dashboard so sánh** - So sánh năng suất, diện tích, tỷ lệ sâu bệnh theo quý/năm

## Công nghệ sử dụng

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM (hỗ trợ SQLite/PostgreSQL)
- **LightGBM** - Dự báo năng suất
- **Holt-Winters** - Dự báo giá thị trường

### Frontend
- **Next.js 14** - React framework (App Router)
- **TypeScript** - Type safety
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
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── ml/             # ML models & data
│   ├── seed_data.py        # Seed dữ liệu mẫu
│   └── requirements.txt
│
└── frontend/                 # Next.js Frontend
    ├── app/                # App Router
    ├── components/         # React components
    ├── lib/                # Utilities & API client
    └── public/             # Static assets
```

## Cách chạy

### Backend

```bash
cd backend

# Tạo virtual environment ( PHẢI DÙNG PYTHON CÓ VER =< 12)
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
| `/detect-disease` | POST | Nhận diện sâu bệnh từ ảnh |
| `/predict-yield` | POST | Dự báo năng suất |
| `/market-price` | GET | Lấy giá thị trường |
| `/dashboard` | GET | Dashboard so sánh kỳ |

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
