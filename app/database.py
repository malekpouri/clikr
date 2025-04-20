from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# مسیر دیتابیس را با توجه به محل اجرای برنامه تنظیم می‌کنیم
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'clikr.db')}"

# ایجاد موتور SQLite
# برای دسترسی چند نخی به دیتابیس connect_args استفاده می‌شود
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# تابع ایجاد نشست دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()