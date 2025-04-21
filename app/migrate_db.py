# app/migrate_geo.py - برنچ geo_info
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
logger = logging.getLogger('geo_migration')

# اضافه کردن مسیر پروژه به sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def migrate_geo_db():
    """اضافه کردن فیلدهای جغرافیایی به جدول click_logs"""
    # مسیر فایل دیتابیس
    db_path = os.path.join(os.path.dirname(__file__), 'clikr.db')

    if not os.path.exists(db_path):
        logger.error(f"دیتابیس در مسیر {db_path} یافت نشد!")
        return False

    try:
        # اتصال به دیتابیس
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # بررسی وجود جدول click_logs
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='click_logs'")
        if cursor.fetchone() is None:
            logger.error("جدول click_logs وجود ندارد!")
            return False

        # اضافه کردن ستون‌های جدید
        columns_to_add = [
            ("country", "TEXT"),
            ("city", "TEXT"),
            ("device_type", "TEXT"),
            ("browser", "TEXT"),
            ("os", "TEXT"),
            ("referrer", "TEXT")
        ]

        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"SELECT {column_name} FROM click_logs LIMIT 1")
                logger.info(f"ستون {column_name} از قبل وجود دارد.")
            except sqlite3.OperationalError:
                # ستون وجود ندارد، آن را اضافه می‌کنیم
                cursor.execute(f"ALTER TABLE click_logs ADD COLUMN {column_name} {column_type}")
                logger.info(f"ستون {column_name} با موفقیت اضافه شد.")

        # ایجاد ایندکس برای بهبود عملکرد جستجو
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_click_logs_country ON click_logs (country)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_click_logs_device ON click_logs (device_type)")
        except sqlite3.OperationalError as e:
            logger.warning(f"خطا در ایجاد ایندکس: {e}")

        conn.commit()
        logger.info("به‌روزرسانی ساختار دیتابیس با موفقیت انجام شد.")

        # بستن اتصال
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"خطا در به‌روزرسانی دیتابیس: {e}")
        return False

if __name__ == "__main__":
    logger.info("شروع به‌روزرسانی دیتابیس برای ذخیره اطلاعات جغرافیایی...")
    success = migrate_geo_db()

    if success:
        logger.info("به‌روزرسانی دیتابیس با موفقیت انجام شد.")
    else:
        logger.error("به‌روزرسانی دیتابیس با خطا مواجه شد.")