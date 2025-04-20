#!/usr/bin/env python3
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import sys

# مدیریت import های نسبی برای حالتی که فایل به صورت مستقیم اجرا شود
if __name__ == "__main__":
    # اضافه کردن مسیر به sys.path
    package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if package_path not in sys.path:
        sys.path.insert(0, package_path)

    # وارد کردن ماژول‌ها به صورت مطلق
    from app import models, services, utils
    from app.database import engine, get_db
else:
    # وارد کردن ماژول‌ها به صورت نسبی (برای uvicorn)
    from . import models, services, utils
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
app.mount("/static", StaticFiles(directory=static_path), name="static")


# مدل پایتونیک برای API
class URLBase(BaseModel):
    url: str


class URLInfo(URLBase):
    short_code: str
    clicks: int


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

    db_url = services.get_url_info(db, short_code)

    url_info = None
    if db_url:
        # ایجاد دیکشنری با نام‌های فیلد مناسب برای تمپلیت
        url_info = {
            "url": db_url.original_url,
            "short_code": db_url.short_code,
            "clicks": db_url.clicks,
            "max_clicks": db_url.max_clicks,
            "expires_at": gregorian_to_jalali(db_url.expires_at),
            "remaining_time": format_remaining_days(db_url.expires_at)
        }

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "url_info": url_info,
            "base_url": str(request.base_url)
        }
    )


# API برای ایجاد URL کوتاه
class URLCreate(URLBase):
    max_clicks: Optional[int] = None


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
        clicks=db_url.clicks
    )

# ارسال فرم برای ایجاد URL کوتاه (از طریق HTML)
@app.post("/", response_class=HTMLResponse)
async def create_short_from_form(
        request: Request,
        url: str = Form(...),
        max_clicks: Optional[int] = Form(None),
        db: Session = Depends(get_db)
):
    if not utils.is_valid_url(url):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Invalid URL format"}
        )

    db_url = services.create_short_url(db, url, max_clicks=max_clicks)
    short_url = f"{request.base_url}{db_url.short_code}"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "short_url": short_url,
            "original_url": db_url.original_url,
            "short_code": db_url.short_code,
            "max_clicks": db_url.max_clicks
        }
    )


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

    return RedirectResponse(db_url.original_url)


# API برای دریافت اطلاعات URL کوتاه
@app.get("/api/info/{short_code}", response_model=Optional[URLInfo])
def get_url_info(short_code: str, db: Session = Depends(get_db)):
    db_url = services.get_url_info(db, short_code)
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    return URLInfo(
        url=db_url.original_url,
        short_code=db_url.short_code,
        clicks=db_url.clicks
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

# اگر به صورت مستقیم اجرا شود (نه با راه‌اندازی از بیرون)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)