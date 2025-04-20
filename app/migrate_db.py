#!/usr/bin/env python3
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

# اضافه کردن مسیر پروژه به sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def migrate_db():
    """اضافه کردن ستون max_clicks به دیتابیس موجود"""
    # مسیر فایل دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), 'clikr.db')

    if not os.path.exists(db_path):
        logger.error(f"دیتابیس در مسیر {db_path} یافت نشد!")
        return False

    try:
        # اتصال به دیتابیس
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # بررسی وجود ستون max_clicks
        cursor.execute("PRAGMA table_info(urls)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        if 'max_clicks' not in column_names:
            logger.info("اضافه کردن ستون max_clicks به جدول urls...")
            cursor.execute("ALTER TABLE urls ADD COLUMN max_clicks INTEGER")
            conn.commit()
            logger.info("ستون max_clicks با موفقیت اضافه شد.")
        else:
            logger.info("ستون max_clicks از قبل وجود دارد.")

        # بستن اتصال
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"خطا در به‌روزرسانی دیتابیس: {e}")
        return False


if __name__ == "__main__":
    logger.info("شروع به‌روزرسانی دیتابیس برای محدودیت تعداد کلیک...")
    success = migrate_db()

    if success:
        logger.info("به‌روزرسانی دیتابیس با موفقیت انجام شد.")
    else:
        logger.error("به‌روزرسانی دیتابیس با خطا مواجه شد.")