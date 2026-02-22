from sqlalchemy import Column, Integer, String, Numeric, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(10), default="C")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_info = Column("metadata", JSON, nullable=True)
    prev_hash = Column(String(64), nullable=False)
    data_hash = Column(String(64), nullable=False)