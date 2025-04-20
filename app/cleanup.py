#!/usr/bin/env python3
import logging
import os
import sys
from datetime import datetime, timedelta

from sqlalchemy import delete, or_

# اضافه کردن مسیر پروژه به sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.models import URL
from app.database import SessionLocal

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('url_cleanup')


def cleanup_expired_urls():
    """حذف لینک‌های منقضی شده"""
    db = SessionLocal()
    try:
        # حذف لینک‌های منقضی شده
        now = datetime.now()
        expired = db.query(URL).filter(
            URL.expires_at < now,
            URL.is_active == True
        ).all()

        for url in expired:
            url.is_active = False
            logger.info(f"Deactivated expired URL: {url.short_code}")

        db.commit()
        logger.info(f"Total deactivated: {len(expired)}")

        # برای حذف کامل از دیتابیس، می‌توان از کد زیر استفاده کرد
        # result = db.execute(delete(URL).where(URL.expires_at < now))
        # db.commit()
        # logger.info(f"Deleted {result.rowcount} expired URLs")
    finally:
        db.close()


def cleanup_inactive_urls(days=180):
    """حذف کامل لینک‌های غیرفعال قدیمی"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # حذف لینک‌هایی که در X روز گذشته غیرفعال بوده‌اند
        result = db.execute(delete(URL).where(
            URL.is_active == False,
            URL.last_accessed < cutoff_date
        ))

        db.commit()
        logger.info(f"Permanently deleted {result.rowcount} old inactive URLs")
    finally:
        db.close()


def cleanup_unused_urls(days=365, min_clicks=1):
    """حذف لینک‌هایی که در X روز گذشته استفاده نشده‌اند و کمتر از Y بار کلیک شده‌اند"""
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # پیدا کردن لینک‌هایی که کمتر استفاده شده‌اند
        unused = db.query(URL).filter(
            or_(
                URL.last_accessed == None,
                URL.last_accessed < cutoff_date
            ),
            URL.clicks < min_clicks
        ).all()

        for url in unused:
            url.is_active = False
            logger.info(f"Deactivated unused URL: {url.short_code}")

        db.commit()
        logger.info(f"Total deactivated unused URLs: {len(unused)}")
    finally:
        db.close()


def vacuum_database():
    """فشرده‌سازی دیتابیس SQLite"""
    # برای SQLite، دستور VACUUM فضای خالی را پس می‌گیرد
    db = SessionLocal()
    try:
        db.execute("VACUUM")
        logger.info("Database has been vacuumed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting URL cleanup process...")

    # خواندن پارامترها از محیط یا استفاده از مقادیر پیش‌فرض
    expiry_days = int(os.environ.get('EXPIRY_DAYS', 90))
    inactive_days = int(os.environ.get('INACTIVE_DAYS', 180))
    unused_days = int(os.environ.get('UNUSED_DAYS', 365))
    min_clicks = int(os.environ.get('MIN_CLICKS', 1))

    logger.info(
        f"Parameters: expiry={expiry_days}d, inactive={inactive_days}d, unused={unused_days}d, min_clicks={min_clicks}")

    # اجرای عملیات پاکسازی
    cleanup_expired_urls()
    cleanup_inactive_urls(days=inactive_days)
    cleanup_unused_urls(days=unused_days, min_clicks=min_clicks)
    vacuum_database()

    logger.info("URL cleanup process completed")