from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, BASE_DIR, UPLOAD_DIR
from app.database import Base, engine
from app import models  # noqa: F401 - đảm bảo models được đăng ký trước create_all
from app.routers import disease, yield_forecast, market_price
from app.routers import frontend_disease, frontend_yield, frontend_market, frontend_dashboard, frontend_crop
from app.routers import assistant

# Import seed_data module để có thể gọi
import seed_data
import seed_market_prices

# Tạo bảng nếu chưa tồn tại (MVP dùng SQLite; khi lên Supabase có thể dùng Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Nông Nghiệp Điện Biên",
    description=(
        "Backend Monolith cho MVP AI Nông Nghiệp Điện Biên: nhận diện sâu bệnh, "
        "dự báo năng suất, phân tích giá thị trường, dashboard so sánh kỳ."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phục vụ ảnh đã upload (demo local; production nên đổi sang Supabase Storage/CDN)
app.mount("/static/uploaded_images", StaticFiles(directory=UPLOAD_DIR), name="uploaded_images")

app.include_router(disease.router)
app.include_router(yield_forecast.router)
app.include_router(market_price.router)

# Frontend API routers (Next.js compatible)
app.include_router(frontend_disease.router)
app.include_router(frontend_disease.report_router)
app.include_router(frontend_yield.router)
app.include_router(frontend_market.router)
app.include_router(frontend_dashboard.router)
app.include_router(frontend_crop.router)

# AI Assistant (chatbot)
app.include_router(assistant.router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Nông Nghiệp Điện Biên API đang chạy"}


@app.post("/admin/seed")
def trigger_seed():
    """Endpoint để seed dữ liệu mẫu. Chỉ dùng trong development/production setup."""
    try:
        seed_data.run()
        return {"status": "ok", "message": "Seed data completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/admin/seed-prices")
def trigger_seed_prices():
    """Seed giá thị trường thực tế vào bảng MarketPrice trong DB."""
    try:
        import seed_market_prices as smp
        smp.run()
        return {"status": "ok", "message": "Market prices seeded into DB"}
    except Exception as e:
        return {"status": "error", "message": str(e)}