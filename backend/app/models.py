from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="farmer")  # farmer | officer
    phone = Column(String, nullable=True)

    farms = relationship("Farm", back_populates="owner")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # rice | coffee | vegetable
    season_info = Column(String, nullable=True)

    farms = relationship("Farm", back_populates="crop")
    market_prices = relationship("MarketPrice", back_populates="crop")


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String, nullable=False)  # vd: "Mường Ảng, Điện Biên"
    area = Column(Float, nullable=False)  # hecta
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)

    owner = relationship("User", back_populates="farms")
    crop = relationship("Crop", back_populates="farms")
    disease_detections = relationship("DiseaseDetection", back_populates="farm")
    yield_predictions = relationship("YieldPrediction", back_populates="farm")


class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    image_url = Column(String, nullable=False)
    disease_label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="disease_detections")


class YieldPrediction(Base):
    __tablename__ = "yield_predictions"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    season = Column(String, nullable=False)  # vd: "2026-Q3"
    predicted_yield = Column(Float, nullable=False)  # tấn
    harvest_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="yield_predictions")


class WeatherHistory(Base):
    __tablename__ = "weather_history"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    temperature = Column(Float, nullable=True)  # độ C trung bình
    rainfall = Column(Float, nullable=True)  # mm


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)  # VND/kg
    source = Column(String, nullable=True)

    crop = relationship("Crop", back_populates="market_prices")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False)  # "quarter" | "year"
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    summary_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
