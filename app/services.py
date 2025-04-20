from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models
from .utils import generate_short_code, normalize_url


# تابع ایجاد URL کوتاه جدید
def create_short_url(db: Session, original_url: str, expiry_days: int = 90) -> models.URL:
    # نرمال‌سازی URL
    normalized_url = normalize_url(original_url)

    # بررسی وجود URL در دیتابیس
    db_url = db.query(models.URL).filter(
        models.URL.original_url == normalized_url,
        models.URL.is_active == True
    ).first()

    if db_url:
        # به‌روزرسانی تاریخ انقضا
        db_url.expires_at = datetime.now() + timedelta(days=expiry_days)
        db.commit()
        db.refresh(db_url)
        return db_url

    # ایجاد کد کوتاه جدید
    for _ in range(5):  # تلاش ۵ بار در صورت تکراری بودن کد
        short_code = generate_short_code()
        expires_at = datetime.now() + timedelta(days=expiry_days)

        db_url = models.URL(
            original_url=normalized_url,
            short_code=short_code,
            expires_at=expires_at
        )
        db.add(db_url)
        try:
            db.commit()
            db.refresh(db_url)
            return db_url
        except IntegrityError:
            db.rollback()  # در صورت تکراری بودن کد، عملیات را برگردان

    # اگر بعد از ۵ تلاش موفق نبود، خطا برگردان
    raise Exception("Failed to generate unique short code after multiple attempts")


# تابع دریافت URL اصلی با استفاده از کد کوتاه
def get_original_url(db: Session, short_code: str) -> str:
    db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    if not db_url or not db_url.is_active:
        return None

    # بررسی تاریخ انقضا
    if db_url.expires_at and db_url.expires_at < datetime.now():
        db_url.is_active = False
        db.commit()
        return None

    # به‌روزرسانی زمان آخرین دسترسی و تعداد کلیک‌ها
    db_url.last_accessed = datetime.now()
    db_url.clicks += 1
    db.commit()

    return db_url.original_url


# تابع دریافت اطلاعات URL با استفاده از کد کوتاه
def get_url_info(db: Session, short_code: str) -> models.URL:
    db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()

    # بررسی تاریخ انقضا
    if db_url and db_url.expires_at and db_url.expires_at < datetime.now():
        db_url.is_active = False
        db.commit()

    return db_url


# تابع تمدید تاریخ انقضای لینک
def extend_url_expiry(db: Session, short_code: str, days: int = 90) -> models.URL:
    db_url = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()

    if not db_url:
        return None

    # تمدید تاریخ انقضا
    db_url.expires_at = datetime.now() + timedelta(days=days)
    db_url.is_active = True  # فعال‌سازی مجدد اگر غیرفعال شده باشد
    db.commit()
    db.refresh(db_url)

    return db_url