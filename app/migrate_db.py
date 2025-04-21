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
    """ایجاد جدول click_logs برای ذخیره تاریخچه بازدیدها"""
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
            logger.info("ایجاد جدول click_logs...")
            cursor.execute("""
                           CREATE TABLE click_logs
                           (
                               id         INTEGER PRIMARY KEY AUTOINCREMENT,
                               url_id     INTEGER NOT NULL,
                               clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               user_agent TEXT,
                               ip_address TEXT,
                               FOREIGN KEY (url_id) REFERENCES urls (id)
                           )
                           """)

            # ایجاد ایندکس برای بهبود عملکرد
            cursor.execute("CREATE INDEX idx_click_logs_url_id ON click_logs (url_id)")
            cursor.execute("CREATE INDEX idx_click_logs_clicked_at ON click_logs (clicked_at)")

            conn.commit()
            logger.info("جدول click_logs با موفقیت ایجاد شد.")
        else:
            logger.info("جدول click_logs از قبل وجود دارد.")

        # بستن اتصال
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"خطا در به‌روزرسانی دیتابیس: {e}")
        return False


if __name__ == "__main__":
    logger.info("شروع به‌روزرسانی دیتابیس برای ذخیره تاریخچه بازدیدها...")
    success = migrate_db()

    if success:
        logger.info("به‌روزرسانی دیتابیس با موفقیت انجام شد.")
    else:
        logger.error("به‌روزرسانی دیتابیس با خطا مواجه شد.")