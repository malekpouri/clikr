from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from . import models
from .utils import generate_short_code, normalize_url


# تابع ایجاد URL کوتاه جدید
def create_short_url(db: Session, original_url: str, expiry_days: int = 90, max_clicks: int = None) -> models.URL:
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
        if max_clicks is not None:
            db_url.max_clicks = max_clicks
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
            expires_at=expires_at,
            max_clicks=max_clicks
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

    # بررسی محدودیت تعداد کلیک
    if db_url.max_clicks is not None:
        if db_url.clicks >= db_url.max_clicks:
            db_url.is_active = False
            db.commit()
            return None

    # به‌روزرسانی زمان آخرین دسترسی و تعداد کلیک‌ها
    db_url.last_accessed = datetime.now()
    db_url.clicks += 1
    db.commit()

    return db_url.original_url


def log_click(db: Session, url_id: int, user_agent: str = None, ip_address: str = None,
              referrer: str = None) -> models.ClickLog:
    """ثبت یک بازدید جدید در تاریخچه با اطلاعات جغرافیایی"""
    from .geo_utils import get_geo_info, parse_user_agent, parse_referrer

    # استخراج اطلاعات جغرافیایی
    geo_info = get_geo_info(ip_address) if ip_address else {'country': None, 'city': None}

    # استخراج اطلاعات دستگاه
    device_info = parse_user_agent(user_agent) if user_agent else {'device_type': None, 'browser': None, 'os': None}

    # پردازش ارجاع دهنده
    processed_referrer = parse_referrer(referrer)

    click_log = models.ClickLog(
        url_id=url_id,
        user_agent=user_agent,
        ip_address=ip_address,
        country=geo_info['country'],
        city=geo_info['city'],
        device_type=device_info['device_type'],
        browser=device_info['browser'],
        os=device_info['os'],
        referrer=processed_referrer
    )

    db.add(click_log)
    db.commit()
    db.refresh(click_log)
    return click_log


def get_geo_stats(db: Session, url_id: int) -> dict:
    """دریافت آمار جغرافیایی کلیک‌ها"""
    from sqlalchemy import func, desc

    # آمار کشورها
    country_stats = (
        db.query(
            models.ClickLog.country,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.country.isnot(None)
        )
        .group_by(models.ClickLog.country)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )

    # آمار شهرها
    city_stats = (
        db.query(
            models.ClickLog.city,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.city.isnot(None)
        )
        .group_by(models.ClickLog.city)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )

    # آمار دستگاه‌ها
    device_stats = (
        db.query(
            models.ClickLog.device_type,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.device_type.isnot(None)
        )
        .group_by(models.ClickLog.device_type)
        .order_by(desc('count'))
        .all()
    )

    # آمار مرورگرها
    browser_stats = (
        db.query(
            models.ClickLog.browser,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.browser.isnot(None)
        )
        .group_by(models.ClickLog.browser)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )

    # آمار سیستم‌عامل‌ها
    os_stats = (
        db.query(
            models.ClickLog.os,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.os.isnot(None)
        )
        .group_by(models.ClickLog.os)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )

    # آمار ارجاع دهنده‌ها
    referrer_stats = (
        db.query(
            models.ClickLog.referrer,
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.referrer.isnot(None)
        )
        .group_by(models.ClickLog.referrer)
        .order_by(desc('count'))
        .limit(10)
        .all()
    )

    return {
        'countries': country_stats,
        'cities': city_stats,
        'devices': device_stats,
        'browsers': browser_stats,
        'os': os_stats,
        'referrers': referrer_stats
    }

def get_click_stats(db: Session, url_id: int, period: str = 'day') -> dict:
    """دریافت آمار کلیک‌ها بر اساس دوره زمانی

    period می‌تواند یکی از مقادیر 'day', 'week', یا 'month' باشد.
    """
    from sqlalchemy import func, cast, Date, extract
    from datetime import datetime, timedelta

    # تاریخ شروع براساس دوره
    now = datetime.now()
    if period == 'day':
        # 24 ساعت گذشته (گروه‌بندی بر اساس ساعت)
        start_date = now - timedelta(days=1)
        date_group = func.strftime('%Y-%m-%d %H:00:00', models.ClickLog.clicked_at)
        date_format = '%H:00'
    elif period == 'week':
        # 7 روز گذشته (گروه‌بندی بر اساس روز)
        start_date = now - timedelta(days=7)
        date_group = func.strftime('%Y-%m-%d', models.ClickLog.clicked_at)
        date_format = '%m-%d'
    else:  # month
        # 30 روز گذشته (گروه‌بندی بر اساس روز)
        start_date = now - timedelta(days=30)
        date_group = func.strftime('%Y-%m-%d', models.ClickLog.clicked_at)
        date_format = '%m-%d'

    # دریافت تعداد کلیک‌ها برای هر بازه زمانی
    results = (
        db.query(
            date_group.label('date'),
            func.count().label('count')
        )
        .filter(
            models.ClickLog.url_id == url_id,
            models.ClickLog.clicked_at >= start_date
        )
        .group_by('date')
        .all()
    )

    # تبدیل نتایج به دیکشنری
    data = {
        'labels': [],
        'counts': []
    }

    result_dict = {r.date: r.count for r in results}

    # ایجاد تمام برچسب‌های زمانی ممکن در بازه، حتی اگر داده‌ای نداشته باشیم
    if period == 'day':
        # 24 ساعت گذشته
        for i in range(24):
            label_time = now - timedelta(hours=24 - i)
            label = label_time.strftime(date_format)
            key = label_time.strftime('%Y-%m-%d %H:00:00')
            data['labels'].append(label)
            data['counts'].append(result_dict.get(key, 0))
    elif period == 'week':
        # 7 روز گذشته
        for i in range(7):
            label_date = now - timedelta(days=7 - i)
            label = label_date.strftime(date_format)
            key = label_date.strftime('%Y-%m-%d')
            data['labels'].append(label)
            data['counts'].append(result_dict.get(key, 0))
    else:  # month
        # 30 روز گذشته
        for i in range(30):
            label_date = now - timedelta(days=30 - i)
            label = label_date.strftime(date_format)
            key = label_date.strftime('%Y-%m-%d')
            data['labels'].append(label)
            data['counts'].append(result_dict.get(key, 0))

    return data

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