from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Mandi(Base):
    __tablename__ = "mandis"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    district = Column(String(100), index=True, nullable=False)
    state = Column(String(100), default="Andhra Pradesh")
    
    # Relationships
    daily_prices = relationship("MandiDailyPrice", back_populates="mandi_rel")


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, index=True) # UUID string
    name = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False) # DEVELOPMENT ONLY: Storing in plaintext
    state = Column(String(100), default="Andhra Pradesh")
    district = Column(String(100), index=True)
    mandi = Column(String(255)) # Storing mandi name or comma-separated mandi names
    crops = Column(String(1000)) # Storing pipe-separated crops string



class MandiDailyPrice(Base):
    __tablename__ = "mandi_daily_prices"

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True)
    date = Column(Date, index=True, nullable=False)
    price = Column(Float, nullable=False) # Modal price
    arrivals = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)

    mandi_rel = relationship("Mandi", back_populates="daily_prices")
    crop_rel = relationship("Crop", back_populates="daily_prices")


class Crop(Base):
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(255), unique=True, index=True, nullable=False)
    name_te = Column(String(255), nullable=True) # Telugu name
    
    daily_prices = relationship("MandiDailyPrice", back_populates="crop_rel")
    predictions = relationship("Prediction", back_populates="crop_rel")


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(Integer, ForeignKey("mandis.id"), index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True)
    target_date = Column(Date, index=True, nullable=False)
    predicted_price = Column(Float, nullable=False)
    confidence_lower = Column(Float, nullable=True)
    confidence_upper = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    crop_rel = relationship("Crop", back_populates="predictions")


class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    district = Column(String(100), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    temp_max = Column(Float)
    temp_min = Column(Float)
    humidity = Column(Float)
    rain_mm = Column(Float)
    wind_speed = Column(Float)


class CropActivityStatus(Base):
    __tablename__ = "crop_activity_status"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), index=True)
    status = Column(String(50)) # active/low/inactive
