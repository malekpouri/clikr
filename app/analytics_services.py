from typing import Dict, Any

from sqlalchemy.orm import Session

from . import models


def log_site_visit(db: Session, path: str, user_agent: str = None, ip_address: str = None,
                   referer: str = None) -> models.SiteVisit:
    """ثبت بازدید از سایت"""
    from .geo_tracker import get_geo_info, parse_user_agent, parse_referer

    # استخراج اطلاعات جغرافیایی
    geo_info = get_geo_info(ip_address) if ip_address else {'country': None, 'city': None}

    # استخراج اطلاعات دستگاه
    device_info = parse_user_agent(user_agent) if user_agent else {
        'device_type': None, 'browser': None, 'os': None
    }

    # استخراج اطلاعات منبع ارجاع
    referer_domain = parse_referer(referer)

    # ایجاد رکورد جدید
    site_visit = models.SiteVisit(
        path=path,
        user_agent=user_agent,
        ip_address=ip_address,
        country=geo_info['country'],
        city=geo_info['city'],
        device_type=device_info['device_type'],
        browser=device_info['browser'],
        os=device_info['os'],
        referer=referer_domain
    )

    db.add(site_visit)
    db.commit()
    db.refresh(site_visit)
    return site_visit


def get_site_visits_stats(db: Session, period: str = 'day') -> dict:
    """دریافت آمار بازدیدهای سایت بر اساس دوره زمانی"""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # تاریخ شروع براساس دوره
    now = datetime.now()
    if period == 'day':
        start_date = now - timedelta(days=1)
        date_group = func.strftime('%Y-%m-%d %H:00:00', models.SiteVisit.visited_at)
        date_format = '%H:00'
    elif period == 'week':
        start_date = now - timedelta(days=7)
        date_group = func.strftime('%Y-%m-%d', models.SiteVisit.visited_at)
        date_format = '%m-%d'
    else:  # month
        start_date = now - timedelta(days=30)
        date_group = func.strftime('%Y-%m-%d', models.SiteVisit.visited_at)
        date_format = '%m-%d'

    # دریافت تعداد بازدیدها برای هر بازه زمانی
    results = (
        db.query(
            date_group.label('date'),
            func.count().label('count')
        )
        .filter(models.SiteVisit.visited_at >= start_date)
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


def get_site_device_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس نوع دستگاه"""
    from sqlalchemy import func

    # آمار بر اساس نوع دستگاه
    device_stats = (
        db.query(
            models.SiteVisit.device_type,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.device_type)
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': [],
        'colors': []
    }

    # رنگ‌های پیش‌فرض برای نمودار
    color_map = {
        'Desktop': '#3f51b5',
        'Mobile': '#ff9800',
        'Tablet': '#4caf50',
        'Bot': '#f44336',
        'Unknown': '#9e9e9e'
    }

    for device in device_stats:
        if device.device_type:
            result['labels'].append(device.device_type)
            result['counts'].append(device.count)
            result['colors'].append(color_map.get(device.device_type, '#9e9e9e'))

    return result


# سایر توابع آماری مشابه get_device_stats، get_browser_stats، get_os_stats، get_country_stats و get_referer_stats را برای site_visits پیاده‌سازی کنید
def get_site_browser_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس مرورگر"""
    from sqlalchemy import func

    # آمار بر اساس مرورگر
    browser_stats = (
        db.query(
            models.SiteVisit.browser,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.browser)
        .order_by(func.count().desc())
        .limit(5)  # فقط 5 مرورگر برتر
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': [],
        'colors': ['#3f51b5', '#ff9800', '#4caf50', '#f44336', '#9c27b0']
    }

    for i, browser in enumerate(browser_stats):
        if browser.browser:
            result['labels'].append(browser.browser)
            result['counts'].append(browser.count)

    return result


def get_site_os_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس سیستم‌عامل"""
    from sqlalchemy import func

    # آمار بر اساس سیستم‌عامل
    os_stats = (
        db.query(
            models.SiteVisit.os,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.os)
        .order_by(func.count().desc())
        .limit(5)  # فقط 5 سیستم‌عامل برتر
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': [],
        'colors': ['#4caf50', '#3f51b5', '#ff9800', '#f44336', '#9c27b0']
    }

    for os_info in os_stats:
        if os_info.os:
            result['labels'].append(os_info.os)
            result['counts'].append(os_info.count)

    return result


def get_site_country_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس کشور"""
    from sqlalchemy import func

    # آمار بر اساس کشور
    country_stats = (
        db.query(
            models.SiteVisit.country,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.country)
        .order_by(func.count().desc())
        .limit(10)  # فقط 10 کشور برتر
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': []
    }

    for country in country_stats:
        if country.country:
            result['labels'].append(country.country)
            result['counts'].append(country.count)

    return result


def get_site_referer_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس منبع ارجاع"""
    from sqlalchemy import func

    # آمار بر اساس منبع ارجاع
    referer_stats = (
        db.query(
            models.SiteVisit.referer,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.referer)
        .order_by(func.count().desc())
        .limit(5)  # فقط 5 منبع برتر
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': [],
        'colors': ['#3f51b5', '#ff9800', '#4caf50', '#f44336', '#9c27b0']
    }

    # اضافه کردن "مستقیم" برای مواردی که referer خالی است
    direct_count = 0

    for referer in referer_stats:
        if referer.referer:
            result['labels'].append(referer.referer)
            result['counts'].append(referer.count)
        else:
            direct_count = referer.count

    # اضافه کردن "مستقیم" اگر وجود داشته باشد
    if direct_count > 0:
        result['labels'].append("مستقیم")
        result['counts'].append(direct_count)

    return result


def get_site_path_stats(db: Session) -> Dict[str, Any]:
    """آمار بازدید سایت بر اساس مسیر"""
    from sqlalchemy import func

    # آمار بر اساس مسیر
    path_stats = (
        db.query(
            models.SiteVisit.path,
            func.count().label('count')
        )
        .group_by(models.SiteVisit.path)
        .order_by(func.count().desc())
        .limit(10)  # فقط 10 مسیر برتر
        .all()
    )

    # تبدیل نتایج به دیکشنری
    result = {
        'labels': [],
        'counts': []
    }

    for path in path_stats:
        if path.path:
            # نمایش مسیر به صورت خلاصه‌تر
            path_label = path.path if len(path.path) < 30 else path.path[:27] + "..."
            result['labels'].append(path_label)
            result['counts'].append(path.count)

    return result


def get_site_total_stats(db: Session) -> Dict[str, Any]:
    """آمار کلی بازدید سایت"""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)

    # تعداد کل بازدیدها
    total_visits = db.query(func.count()).select_from(models.SiteVisit).scalar() or 0

    # تعداد بازدیدهای امروز
    today_visits = db.query(func.count()).select_from(models.SiteVisit).filter(
        func.date(models.SiteVisit.visited_at) == func.date(now)
    ).scalar() or 0

    # تعداد بازدیدهای دیروز
    yesterday_visits = db.query(func.count()).select_from(models.SiteVisit).filter(
        func.date(models.SiteVisit.visited_at) == func.date(yesterday)
    ).scalar() or 0

    # تعداد بازدیدهای هفته اخیر
    week_visits = db.query(func.count()).select_from(models.SiteVisit).filter(
        models.SiteVisit.visited_at >= last_week
    ).scalar() or 0

    # تعداد بازدیدهای ماه اخیر
    month_visits = db.query(func.count()).select_from(models.SiteVisit).filter(
        models.SiteVisit.visited_at >= last_month
    ).scalar() or 0

    # تعداد کاربران منحصر به فرد (تقریبی بر اساس IP)
    unique_users = db.query(func.count(func.distinct(models.SiteVisit.ip_address))).select_from(
        models.SiteVisit).scalar() or 0

    return {
        "total_visits": total_visits,
        "today_visits": today_visits,
        "yesterday_visits": yesterday_visits,
        "week_visits": week_visits,
        "month_visits": month_visits,
        "unique_users": unique_users
    }