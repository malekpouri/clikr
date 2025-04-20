FROM python:3.11-slim

WORKDIR /app

# کپی فایل‌های مورد نیاز
COPY requirements.txt .

# نصب پکیج‌های مورد نیاز
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل پروژه
COPY . .

# ساخت فولدرهای مورد نیاز
RUN mkdir -p app/static app/templates

# مشخص کردن پورت
EXPOSE 8000

# محدود کردن منابع مصرفی
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# راه‌اندازی برنامه
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]