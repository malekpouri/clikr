FROM python:3.11-slim

WORKDIR /app

# نصب cron و تنظیم پیش‌نیازها
RUN apt-get update && apt-get -y install curl cron && apt-get clean

# کپی فایل‌های مورد نیاز
COPY requirements.txt .

# نصب پکیج‌های مورد نیاز
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل پروژه
COPY . .

# ساخت فولدرهای مورد نیاز
RUN mkdir -p app/static app/templates logs

# دانلود فایل GeoLite2-City.mmdb
RUN curl -L -o app/static/GeoLite2-City.mmdb https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb

# تنظیم cron job
RUN echo "0 2 * * 0 cd /app && python /app/app/cleanup.py >> /app/logs/cleanup.log 2>&1" > /etc/cron.d/clikr-cron
RUN chmod 0644 /etc/cron.d/clikr-cron
RUN crontab /etc/cron.d/clikr-cron

# ایجاد فایل لاگ
RUN mkdir -p /app/logs
RUN touch /app/logs/cleanup.log
RUN chmod 0666 /app/logs/cleanup.log

# مشخص کردن پورت
EXPOSE 8000

# محدود کردن منابع مصرفی
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# اسکریپت راه‌اندازی
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# راه‌اندازی برنامه
CMD ["/entrypoint.sh"]