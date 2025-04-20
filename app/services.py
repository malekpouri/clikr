from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models
from .utils import generate_short_code, normalize_url


# تابع ایجاد URL کوتاه جدید
def create_short_url(db: Session, original_url: str) -> models.URL:
    # نرمال‌سازی URL
    normalized_url = normalize_url(original_url)

    # بررسی وجود URL در دیتابیس
    db_url = db.query(models.URL).filter(models.URL.original_url == normalized_url).first()
    if db_url:
        return db_url

    # ایجاد کد کوتاه جدید
    for _ in range(5):  # تلاش ۵ بار در صورت تکراری بودن کد
        short_code = generate_short_code()
        db_url = models.URL(
            original_url=normalized_url,
            short_code=short_code
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

    # به‌روزرسانی زمان آخرین دسترسی و تعداد کلیک‌ها
    db_url.last_accessed = datetime.now()
    db_url.clicks += 1
    db.commit()

    return db_url.original_url


# تابع دریافت اطلاعات URL با استفاده از کد کوتاه
def get_url_info(db: Session, short_code: str) -> models.URL:
    return db.query(models.URL).filter(models.URL.short_code == short_code).first()