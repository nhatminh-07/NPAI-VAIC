"""
Script sync database schema lên Supabase PostgreSQL.
Chạy: python sync_schema.py
"""
from sqlalchemy import text
from app.database import engine, Base

def sync_schema():
    print("🔄 Đang kết nối Supabase...")

    with engine.connect() as conn:
        # Tạo từng bảng
        tables = [
            # Users
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                role VARCHAR NOT NULL DEFAULT 'farmer',
                phone VARCHAR
            )""",

            # Crops
            """CREATE TABLE IF NOT EXISTS crops (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                season_info VARCHAR
            )""",

            # Farms
            """CREATE TABLE IF NOT EXISTS farms (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                location VARCHAR NOT NULL,
                area FLOAT NOT NULL,
                crop_id INTEGER REFERENCES crops(id)
            )""",

            # DiseaseDetections
            """CREATE TABLE IF NOT EXISTS disease_detections (
                id SERIAL PRIMARY KEY,
                farm_id INTEGER REFERENCES farms(id),
                image_url VARCHAR NOT NULL,
                disease_label VARCHAR NOT NULL,
                confidence FLOAT NOT NULL,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            # YieldPredictions
            """CREATE TABLE IF NOT EXISTS yield_predictions (
                id SERIAL PRIMARY KEY,
                farm_id INTEGER REFERENCES farms(id),
                season VARCHAR NOT NULL,
                predicted_yield FLOAT NOT NULL,
                harvest_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",

            # WeatherHistory
            """CREATE TABLE IF NOT EXISTS weather_history (
                id SERIAL PRIMARY KEY,
                location VARCHAR NOT NULL,
                date DATE NOT NULL,
                temperature FLOAT,
                rainfall FLOAT
            )""",

            # MarketPrice
            """CREATE TABLE IF NOT EXISTS market_prices (
                id SERIAL PRIMARY KEY,
                crop_id INTEGER REFERENCES crops(id),
                date DATE NOT NULL,
                price FLOAT NOT NULL,
                source VARCHAR
            )""",

            # Reports
            """CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                period VARCHAR NOT NULL,
                crop_id INTEGER REFERENCES crops(id),
                summary_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]

        for sql in tables:
            try:
                conn.execute(text(sql))
                table_name = sql.split("IF NOT EXISTS")[1].split("(")[0].strip()
                print(f"  ✅ Tạo bảng: {table_name}")
            except Exception as e:
                print(f"  ⚠️ Lỗi: {e}")

        conn.commit()

        # Insert dữ liệu mẫu crops nếu chưa có
        crops_check = conn.execute(text("SELECT COUNT(*) FROM crops")).scalar()
        if crops_check == 0:
            crops_data = [
                ("rice", "Vụ chiêm xuân + vụ mùa"),
                ("coffee", "Thu hoạch tháng 10-12"),
                ("vegetable", "Vụ đông, luân canh nhiều đợt/năm"),
            ]
            for name, info in crops_data:
                conn.execute(text(
                    "INSERT INTO crops (name, season_info) VALUES (:name, :info)"
                ), {"name": name, "info": info})
            conn.commit()
            print("  ✅ Đã insert dữ liệu mẫu crops")
        else:
            print("  ℹ️ Crops đã có dữ liệu, bỏ qua")

    print("\n✅ Sync schema hoàn tất!")

if __name__ == "__main__":
    sync_schema()
