#!/usr/bin/env python3
import os
import sys
import uvicorn

# اضافه کردن ریشه پروژه به sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    # فقط برای تایید مسیر
    print(f"Project root: {project_root}")

    # اجرای برنامه با یوویکورن
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)