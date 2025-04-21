from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
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


class ClickLog(Base):
    __tablename__ = "click_logs"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    clicked_at = Column(DateTime(timezone=True), default=func.now())
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    # اطلاعات جغرافیایی
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    referrer = Column(String, nullable=True)

    # رابطه با مدل URL
    url = relationship("URL", back_populates="click_logs")


# اضافه کردن رابطه به مدل URL
URL.click_logs = relationship("ClickLog", back_populates="url")