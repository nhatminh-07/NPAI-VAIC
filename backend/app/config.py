import os

# Thư mục gốc của app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Database ---
# MVP dùng SQLite cho demo local/48h. Khi triển khai thật, đổi DATABASE_URL
# sang chuỗi kết nối Supabase Postgres, ví dụ:
# postgresql://postgres:<password>@<host>:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/dienbien_agri.db")

# --- Storage ảnh (demo dùng local disk, sau này đổi sang Supabase Storage) ---
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- ML artifacts ---
ML_DIR = os.path.join(BASE_DIR, "app", "ml")
YIELD_MODEL_PATH = os.path.join(ML_DIR, "yield_model.joblib")

# --- Data mẫu ---
DATA_DIR = os.path.join(BASE_DIR, "app", "data")
SAMPLE_PRICE_CSV = os.path.join(DATA_DIR, "sample_prices.csv")
SAMPLE_YIELD_CSV = os.path.join(DATA_DIR, "sample_yield_history.csv")
DISEASE_RULES_JSON = os.path.join(DATA_DIR, "disease_recommendations.json")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
