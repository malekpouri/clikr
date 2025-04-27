#!/usr/bin/env python3
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import sys
from fastapi import Response
from .middlewares import AnalyticsMiddleware

# مدیریت import های نسبی برای حالتی که فایل به صورت مستقیم اجرا شود
if __name__ == "__main__":
    # اضافه کردن مسیر به sys.path
    package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if package_path not in sys.path:
        sys.path.insert(0, package_path)

    # وارد کردن ماژول‌ها به صورت مطلق
    from app import models, services, utils ,analytics_services
    from app.database import engine, get_db
else:
    # وارد کردن ماژول‌ها به صورت نسبی (برای uvicorn)
    from . import models, services, utils ,analytics_services
    from .database import engine, get_db

# ایجاد دیتابیس اگر وجود نداشته باشد
models.Base.metadata.create_all(bind=engine)

# ایجاد اپلیکیشن FastAPI
app = FastAPI(title="clikr - URL Shortener")

# تنظیم فولدر templates برای فایل‌های HTML
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# اضافه کردن فولدر static برای فایل‌های CSS و JS
static_path = os.path.join(os.path.dirname(__file__), "static")
app.add_middleware(AnalyticsMiddleware)
app.mount("/static", StaticFiles(directory=static_path), name="static")


# مدل پایتونیک برای API
class URLBase(BaseModel):
    url: str


# API برای ایجاد URL کوتاه
class URLCreate(URLBase):
    max_clicks: Optional[int] = None


class URLInfo(URLBase):
    short_code: str
    clicks: int
    max_clicks: Optional[int] = None
    expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }


# صفحه اصلی
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# صفحه آمار با پارامتر کد کوتاه
@app.get("/stats", response_class=HTMLResponse)
async def show_stats_by_code(request: Request, code: str = None, db: Session = Depends(get_db)):
    if not code:
        return templates.TemplateResponse(
            "stats.html",
            {
                "request": request,
                "url_info": None,
                "base_url": str(request.base_url),
                "error": "لطفاً یک کد کوتاه وارد کنید."
            }
        )

    # هدایت به آدرس /stats/{short_code}
    return RedirectResponse(url=f"/stats/{code}")


# صفحه آمار
@app.get("/stats/{short_code}", response_class=HTMLResponse)
async def show_stats(request: Request, short_code: str, db: Session = Depends(get_db)):
    from .date_utils import gregorian_to_jalali, format_remaining_days
    from .qr_generator import generate_qr_code

    db_url = services.get_url_info(db, short_code)

    url_info = None
    if db_url:
        full_url = f"{request.base_url}{db_url.short_code}"
        qr_code = generate_qr_code(full_url)

        # ایجاد دیکشنری با نام‌های فیلد مناسب برای تمپلیت
        url_info = {
            "url": db_url.original_url,
            "short_code": db_url.short_code,
            "clicks": db_url.clicks,
            "max_clicks": db_url.max_clicks,
            "expires_at": gregorian_to_jalali(db_url.expires_at),
            "remaining_time": format_remaining_days(db_url.expires_at),
            "qr_code": qr_code,
            "full_url": full_url,
            "id": db_url.id
        }

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "url_info": url_info,
            "base_url": str(request.base_url)
        }
    )


@app.get("/api/docs", response_class=HTMLResponse)
async def api_docs(request: Request):
    """صفحه مستندات API"""
    return templates.TemplateResponse(
        "api_docs.html",
        {
            "request": request,
            "base_url": str(request.base_url)
        }
    )


@app.get("/qr/{short_code}")
async def download_qr_code(request: Request, short_code: str, db: Session = Depends(get_db)):
    from .qr_generator import generate_qr_code_file

    db_url = services.get_url_info(db, short_code)

    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    # ساخت URL کامل
    base_url = str(request.base_url).rstrip('/')
    full_url = f"{base_url}/{short_code}"

    # تولید کد QR
    qr_file = generate_qr_code_file(full_url)

    # استفاده از StreamingResponse به جای Response
    return StreamingResponse(
        qr_file,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="clikr-{short_code}.png"'
        }
    )


@app.post("/api/shorten", response_model=URLInfo)
def create_short(url_data: URLCreate, db: Session = Depends(get_db)):
    if not utils.is_valid_url(url_data.url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    db_url = services.create_short_url(
        db,
        url_data.url,
        expiry_days=90,
        max_clicks=url_data.max_clicks
    )
    return URLInfo(
        url=db_url.original_url,
        short_code=db_url.short_code,
        clicks=db_url.clicks,
        max_clicks=db_url.max_clicks,
        expires_at=db_url.expires_at
    )


# ارسال فرم برای ایجاد URL کوتاه (از طریق HTML)
@app.post("/", response_class=HTMLResponse)
async def create_short_from_form(
        request: Request,
        url: str = Form(...),
        max_clicks: Optional[str] = Form(None),  # تغییر از int به str
        db: Session = Depends(get_db)
):
    if not utils.is_valid_url(url):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "فرمت آدرس وارد شده صحیح نیست"}
        )

    # تبدیل max_clicks به عدد صحیح در صورتی که خالی نباشد
    max_clicks_int = None
    if max_clicks and max_clicks.strip():
        try:
            max_clicks_int = int(max_clicks)
            if max_clicks_int <= 0:
                return templates.TemplateResponse(
                    "index.html",
                    {"request": request, "error": "تعداد کلیک باید عدد مثبت باشد"}
                )
        except ValueError:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "error": "تعداد کلیک باید یک عدد صحیح باشد"}
            )

    db_url = services.create_short_url(db, url, max_clicks=max_clicks_int)
    short_url = f"{request.base_url}{db_url.short_code}"

    # تولید کد QR برای صفحه اصلی
    from .qr_generator import generate_qr_code
    qr_code = generate_qr_code(short_url)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "short_url": short_url,
            "original_url": db_url.original_url,
            "short_code": db_url.short_code,
            "max_clicks": db_url.max_clicks,
            "qr_code": qr_code
        }
    )


@app.get("/robots.txt")
async def robots_txt():
    content = """
User-agent: *
Disallow: /admin/
Allow: /
Sitemap: https://clikr.ir/sitemap.xml
"""
    return Response(content=content.strip(), media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap_xml():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://clikr.ir/</loc>
        <lastmod>2025-04-20</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>    
</urlset>
"""
    return Response(content=content.strip(), media_type="application/xml")


# هدایت به URL اصلی با استفاده از کد کوتاه
@app.get("/{short_code}")
def redirect_to_original(request: Request, short_code: str, db: Session = Depends(get_db)):
    db_url = services.get_url_info(db, short_code)

    # اگر لینک یافت نشد
    if not db_url:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "لینک یافت نشد",
                "error_message": "لینک مورد نظر در سیستم وجود ندارد یا حذف شده است.",
                "error_type": "not_found"
            },
            status_code=404
        )

    # بررسی تاریخ انقضا
    if db_url.expires_at and db_url.expires_at < datetime.now():
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "لینک منقضی شده",
                "error_message": "تاریخ انقضای این لینک به پایان رسیده است.",
                "error_type": "expired"
            },
            status_code=410
        )

    # بررسی محدودیت تعداد کلیک
    if db_url.max_clicks is not None and db_url.clicks >= db_url.max_clicks:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "محدودیت تعداد کلیک",
                "error_message": "این لینک به محدودیت تعداد کلیک رسیده و غیرفعال شده است.",
                "error_type": "max_clicks"
            },
            status_code=410
        )

    # به‌روزرسانی زمان آخرین دسترسی و تعداد کلیک‌ها
    db_url.last_accessed = datetime.now()
    db_url.clicks += 1
    db.commit()

    user_agent = request.headers.get("user-agent", "")
    client_host = request.client.host if request.client else None
    referrer = request.headers.get("referer", None)  # دریافت ارجاع دهنده

    services.log_click(db, db_url.id, user_agent, client_host, referrer)

    return RedirectResponse(db_url.original_url)


@app.get("/api/geo/{short_code}")
def get_geo_stats_api(short_code: str, db: Session = Depends(get_db)):
    """API برای دریافت آمار جغرافیایی کلیک‌ها"""
    db_url = services.get_url_info(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    stats = services.get_geo_stats(db, db_url.id)

    # تبدیل به فرمت مناسب جیسون
    result = {}
    for key, values in stats.items():
        result[key] = [{"name": item[0] or "نامشخص", "count": item[1]} for item in values]

    return result


@app.get("/api/stats/{short_code}/{period}")
def get_click_stats_api(short_code: str, period: str, db: Session = Depends(get_db)):
    """API برای دریافت آمار کلیک‌ها

    period: 'day', 'week', یا 'month'
    """
    if period not in ['day', 'week', 'month']:
        raise HTTPException(status_code=400, detail="Invalid period. Use 'day', 'week', or 'month'")

    db_url = services.get_url_info(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    stats = services.get_click_stats(db, db_url.id, period)
    return stats


# API برای دریافت اطلاعات URL کوتاه
@app.get("/api/info/{short_code}", response_model=Optional[URLInfo])
def get_url_info(short_code: str, db: Session = Depends(get_db)):
    db_url = services.get_url_info(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    return URLInfo(
        url=db_url.original_url,
        short_code=db_url.short_code,
        clicks=db_url.clicks,
        max_clicks=db_url.max_clicks,
        expires_at=db_url.expires_at
    )


# مدل برای درخواست تمدید
class ExtendExpiryRequest(BaseModel):
    days: int = 90


# API برای تمدید تاریخ انقضای لینک
@app.post("/api/extend/{short_code}", response_model=Optional[URLInfo])
def extend_expiry(short_code: str, request_data: ExtendExpiryRequest, db: Session = Depends(get_db)):
    db_url = services.extend_url_expiry(db, short_code, request_data.days)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    return URLInfo(
        url=db_url.original_url,
        short_code=db_url.short_code,
        clicks=db_url.clicks
    )


# صفحه تمدید تاریخ انقضا
@app.get("/extend/{short_code}", response_class=HTMLResponse)
async def extend_expiry_page(request: Request, short_code: str, db: Session = Depends(get_db)):
    from .date_utils import gregorian_to_jalali, format_remaining_days

    db_url = services.get_url_info(db, short_code)

    url_info = None
    if db_url:
        # ایجاد دیکشنری با نام‌های فیلد مناسب برای تمپلیت
        url_info = {
            "url": db_url.original_url,
            "short_code": db_url.short_code,
            "clicks": db_url.clicks,
            "expires_at": gregorian_to_jalali(db_url.expires_at),
            "remaining_time": format_remaining_days(db_url.expires_at)
        }

    return templates.TemplateResponse(
        "extend.html",
        {
            "request": request,
            "url_info": url_info,
            "base_url": str(request.base_url)
        }
    )


# تمدید تاریخ انقضا از طریق فرم
@app.post("/extend/{short_code}", response_class=HTMLResponse)
async def extend_expiry_form(
        request: Request,
        short_code: str,
        days: int = Form(90),
        db: Session = Depends(get_db)
):
    db_url = services.extend_url_expiry(db, short_code, days)

    if not db_url:
        return templates.TemplateResponse(
            "extend.html",
            {
                "request": request,
                "url_info": None,
                "base_url": str(request.base_url),
                "error": "لینک مورد نظر یافت نشد."
            }
        )

    url_info = {
        "url": db_url.original_url,
        "short_code": db_url.short_code,
        "clicks": db_url.clicks,
        "expires_at": db_url.expires_at.strftime("%Y-%m-%d %H:%M:%S") if db_url.expires_at else "بدون تاریخ انقضا"
    }

    return templates.TemplateResponse(
        "extend.html",
        {
            "request": request,
            "url_info": url_info,
            "base_url": str(request.base_url),
            "success": f"تاریخ انقضای لینک با موفقیت به {days} روز دیگر تمدید شد."
        }
    )


# اضافه کردن به main.py

@app.get("/api/site-stats/visits/{period}")
def get_site_visits_api(period: str, db: Session = Depends(get_db)):
    """API برای دریافت آمار بازدیدهای سایت"""
    if period not in ['day', 'week', 'month']:
        raise HTTPException(status_code=400, detail="Invalid period. Use 'day', 'week', or 'month'")

    stats = analytics_services.get_site_visits_stats(db, period)
    return stats


@app.get("/api/site-stats/devices")
def get_site_devices_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار دستگاه‌های بازدیدکنندگان سایت"""
    stats = analytics_services.get_site_device_stats(db)
    return stats


@app.get("/api/site-stats/browsers")
def get_site_browsers_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار مرورگرهای بازدیدکنندگان سایت"""
    stats = analytics_services.get_site_browser_stats(db)
    return stats


@app.get("/api/site-stats/os")
def get_site_os_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار سیستم‌عامل‌های بازدیدکنندگان سایت"""
    stats = analytics_services.get_site_os_stats(db)
    return stats


@app.get("/api/site-stats/countries")
def get_site_countries_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار کشورهای بازدیدکنندگان سایت"""
    stats = analytics_services.get_site_country_stats(db)
    return stats


@app.get("/api/site-stats/referers")
def get_site_referers_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار منابع ارجاع بازدیدکنندگان سایت"""
    stats = analytics_services.get_site_referer_stats(db)
    return stats


@app.get("/api/site-stats/paths")
def get_site_paths_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار مسیرهای بازدیدشده سایت"""
    stats = analytics_services.get_site_path_stats(db)
    return stats


@app.get("/api/site-stats/total")
def get_site_total_stats_api(db: Session = Depends(get_db)):
    """API برای دریافت آمار کلی بازدید سایت"""
    stats = analytics_services.get_site_total_stats(db)
    return stats


# اضافه کردن به main.py

@app.get("/admin/analytics", response_class=HTMLResponse)
async def site_analytics(request: Request, db: Session = Depends(get_db)):
    """صفحه آمار بازدیدهای سایت"""
    # بررسی دسترسی (اینجا ساده در نظر گرفته شده)
    # در حالت واقعی، باید سیستم احراز هویت مناسب استفاده شود

    # آمار کلی
    total_stats = analytics_services.get_site_total_stats(db)

    return templates.TemplateResponse(
        "site_analytics.html",
        {
            "request": request,
            "total_stats": total_stats
        }
    )

# اگر به صورت مستقیم اجرا شود (نه با راه‌اندازی از بیرون)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
