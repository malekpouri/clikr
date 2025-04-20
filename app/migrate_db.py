#!/usr/bin/env python3
"""
اسکریپت به‌روزرسانی دیتابیس برای اضافه کردن فیلد تاریخ انقضا
این اسکریپت فقط یک بار و پس از به‌روزرسانی کدهای برنامه باید اجرا شود
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta
import logging

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('db_migration')

# اضافه کردن مسیر پروژه به sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def migrate_db():
    """اضافه کردن ستون expires_at به دیتابیس موجود"""
    # مسیر فایل دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), 'clikr.db')

    if not os.path.exists(db_path):
        logger.error(f"دیتابیس در مسیر {db_path} یافت نشد!")
        return False

    try:
        # اتصال به دیتابیس
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # بررسی وجود ستون expires_at
        cursor.execute("PRAGMA table_info(urls)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        if 'expires_at' not in column_names:
            logger.info("اضافه کردن ستون expires_at به جدول urls...")
            cursor.execute("ALTER TABLE urls ADD COLUMN expires_at TIMESTAMP")

            # تنظیم تاریخ انقضا برای رکوردهای موجود (90 روز از تاریخ فعلی)
            expiry_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE urls SET expires_at = ? WHERE expires_at IS NULL", (expiry_date,))

            conn.commit()
            logger.info(f"ستون expires_at با موفقیت اضافه شد. تاریخ انقضای پیش‌فرض: {expiry_date}")
        else:
            logger.info("ستون expires_at از قبل وجود دارد.")

        # بستن اتصال
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"خطا در به‌روزرسانی دیتابیس: {e}")
        return False


if __name__ == "__main__":
    logger.info("شروع به‌روزرسانی دیتابیس...")
    success = migrate_db()

    if success:
        logger.info("به‌روزرسانی دیتابیس با موفقیت انجام شد.")
    else:
        logger.error("به‌روزرسانی دیتابیس با خطا مواجه شد.")