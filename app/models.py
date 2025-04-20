from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from .database import Base

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, index=True)
    short_code = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # تاریخ انقضا
    clicks = Column(Integer, default=0)
    max_clicks = Column(Integer, nullable=True)  # حداکثر تعداد کلیک مجاز
    is_active = Column(Boolean, default=True)

    @classmethod
    def create_with_expiry(cls, original_url, short_code, expiry_days=90):
        """ایجاد یک URLبا تاریخ انقضای مشخص"""
        expires_at = datetime.now() + timedelta(days=expiry_days)
        return cls(
            original_url=original_url,
            short_code=short_code,
            expires_at=expires_at
        )