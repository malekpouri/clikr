# app/migrate_site_analytics.py
# !/usr/bin/env python3
import os
import sys
import sqlite3
import logging

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('db_migration')


def migrate_db():
    """ایجاد جدول site_visits برای ذخیره آمار بازدیدهای سایت"""
    # مسیر فایل دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), 'clikr.db')

    if not os.path.exists(db_path):
        logger.error(f"دیتابیس در مسیر {db_path} یافت نشد!")
        return False

    try:
        # اتصال به دیتابیس
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # بررسی وجود جدول site_visits
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='site_visits'")
        if cursor.fetchone() is None:
            logger.info("ایجاد جدول site_visits...")
            cursor.execute("""
                           CREATE TABLE site_visits
                           (
                               id          INTEGER PRIMARY KEY AUTOINCREMENT,
                               visited_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               path        TEXT,
                               user_agent  TEXT,
                               ip_address  TEXT,
                               country     TEXT,
                               city        TEXT,
                               device_type TEXT,
                               browser     TEXT,
                               os          TEXT,
                               referer     TEXT
                           )
                           """)

            # ایجاد ایندکس برای بهبود عملکرد
            cursor.execute("CREATE INDEX idx_site_visits_visited_at ON site_visits (visited_at)")
            cursor.execute("CREATE INDEX idx_site_visits_path ON site_visits (path)")

            conn.commit()
            logger.info("جدول site_visits با موفقیت ایجاد شد.")
        else:
            logger.info("جدول site_visits از قبل وجود دارد.")

        # بستن اتصال
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"خطا در به‌روزرسانی دیتابیس: {e}")
        return False


if __name__ == "__main__":
    logger.info("شروع به‌روزرسانی دیتابیس برای آمار بازدیدهای سایت...")
    success = migrate_db()

    if success:
        logger.info("به‌روزرسانی دیتابیس با موفقیت انجام شد.")
    else:
        logger.error("به‌روزرسانی دیتابیس با خطا مواجه شد.")