#!/usr/bin/env python3
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
    db_url = services.get_url_info(db, short_code)

    url_info = None
    if db_url:
        # ایجاد دیکشنری با نام‌های فیلد مناسب برای تمپلیت
        url_info = {
            "url": db_url.original_url,
            "short_code": db_url.short_code,
            "clicks": db_url.clicks
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
@app.post("/api/shorten", response_model=URLInfo)
def create_short(url_data: URLBase, db: Session = Depends(get_db)):
    if not utils.is_valid_url(url_data.url):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    db_url = services.create_short_url(db, url_data.url)
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
        db: Session = Depends(get_db)
):
    if not utils.is_valid_url(url):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Invalid URL format"}
        )

    db_url = services.create_short_url(db, url)
    short_url = f"{request.base_url}{db_url.short_code}"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "short_url": short_url,
            "original_url": db_url.original_url,
            "short_code": db_url.short_code
        }
    )


# هدایت به URL اصلی با استفاده از کد کوتاه
@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    original_url = services.get_original_url(db, short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="URL not found")

    return RedirectResponse(original_url)


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


# اگر به صورت مستقیم اجرا شود (نه با راه‌اندازی از بیرون)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)