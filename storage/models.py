from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func, Float, BigInteger
import uuid

class Base(DeclarativeBase):
    pass

class TrackLocations(Base):
    __tablename__ = "track_locations"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id = mapped_column(String(50), nullable=False)
    latitude = mapped_column(Float, nullable=False)
    longitude = mapped_column(Float, nullable=False)
    location_name = mapped_column(String(100), nullable=True)
    timestamp = mapped_column(DateTime, nullable=False)
    trace_id = mapped_column(BigInteger, nullable=False)  
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

class TrackAlerts(Base):
    __tablename__ = "track_alerts"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id = mapped_column(String(50), nullable=False)
    latitude = mapped_column(Float, nullable=False)
    longitude = mapped_column(Float, nullable=False)
    location_name = mapped_column(String(100), nullable=True)
    alert_desc = mapped_column(String(100), nullable=True)
    timestamp = mapped_column(DateTime, nullable=False)
    trace_id = mapped_column(BigInteger, nullable=False) 
    date_created = mapped_column(DateTime, nullable=False, default=func.now())