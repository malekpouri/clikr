# clikr - سرویس کوتاه‌کننده لینک

<div align="center">
  <img src="app/static/favicon/android-chrome-192x192.png" alt="clikr logo" width="100" />
  <h3>سرویس ساده و سبک کوتاه کردن لینک</h3>
</div>

clikr یک سرویس کوتاه‌کننده لینک ساده، سریع و کم‌مصرف است که با FastAPI و SQLite پیاده‌سازی شده است. این سرویس برای اجرا در سرورهای با منابع محدود بهینه‌سازی شده و با کمتر از 100MB حافظه قابل اجراست.

## ویژگی‌ها

- 🚀 کوتاه کردن لینک‌های طولانی
- 📊 ردیابی تعداد کلیک‌ها روی هر لینک
- 📱 رابط کاربری ریسپانسیو و زیبا
- 🔌 API برای استفاده در سایر برنامه‌ها
- 🔍 امکان جستجوی آمار لینک‌ها
- 📦 امکان اجرا با داکر
- 💾 مصرف منابع بسیار کم

## پیش‌نیازها

- Python 3.9+
- FastAPI
- SQLite
- یا Docker برای اجرا با کانتینر

## نصب و راه‌اندازی

### روش ۱: اجرا با پایتون

1. کلون کردن مخزن:
   ```bash
   git clone https://github.com/malekpouri/clikr.git
   cd clikr
   ```

2. ساخت محیط مجازی:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # یا
   .venv\Scripts\activate  # Windows
   ```

3. نصب وابستگی‌ها:
   ```bash
   pip install -r requirements.txt
   ```

4. اجرای برنامه:
   ```bash
   python run.py
   ```
   یا
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### روش ۲: اجرا با داکر

1. ساخت و اجرای کانتینر:
   ```bash
   docker-compose up -d
   ```

2. مشاهده لاگ‌ها:
   ```bash
   docker-compose logs -f
   ```

## استفاده از API

### کوتاه کردن لینک

```bash
curl -X POST "http://localhost:8000/api/shorten" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/your-very-long-url-that-needs-shortening"}'
```

پاسخ:
```json
{
  "url": "https://example.com/your-very-long-url-that-needs-shortening",
  "short_code": "Ab3X9z",
  "clicks": 0
}
```

### دریافت اطلاعات لینک کوتاه

```bash
curl "http://localhost:8000/api/info/Ab3X9z"
```

پاسخ:
```json
{
  "url": "https://example.com/your-very-long-url-that-needs-shortening",
  "short_code": "Ab3X9z",
  "clicks": 5
}
```

## مستندات

مستندات Swagger API در آدرس زیر قابل دسترسی است:
```
http://localhost:8000/docs
```

## ساختار پروژه

```
clikr/
├── app/                  # پکیج اصلی برنامه
│   ├── __init__.py
│   ├── main.py           # اندپوینت‌های اصلی
│   ├── models.py         # مدل‌های دیتابیس
│   ├── database.py       # تنظیمات دیتابیس
│   ├── services.py       # منطق کسب و کار
│   ├── utils.py          # توابع کمکی
│   ├── templates/        # قالب‌های HTML
│   └── static/           # فایل‌های استاتیک (CSS, JS)
├── requirements.txt      # وابستگی‌های پایتون
├── run.py                # اسکریپت اجرای برنامه
├── Dockerfile            # فایل داکر
└── docker-compose.yml    # تنظیمات داکر کامپوز
```

## محدودیت منابع

برنامه clikr برای اجرا در سرورهای با منابع محدود بهینه‌سازی شده است:
- مصرف حافظه: کمتر از 100MB
- مصرف CPU: حداقل

## توسعه‌دهندگان

[malekpouri](https://github.com/malekpouri)

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.