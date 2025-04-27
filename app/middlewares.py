
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from . import analytics_services as services
from .database import SessionLocal


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # نادیده گرفتن درخواست‌های استاتیک
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # نادیده گرفتن درخواست‌های API
        if request.url.path.startswith("/api"):
            return await call_next(request)

        # ذخیره اطلاعات درخواست
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        client_host = request.client.host if request.client else None
        referer = request.headers.get("referer")

        # اجرای درخواست
        response = await call_next(request)

        # فقط درخواست‌های موفق را ثبت کنیم
        if response.status_code < 400:
            try:
                # ثبت بازدید در پس‌زمینه
                db = SessionLocal()
                services.log_site_visit(db, path, user_agent, client_host, referer)
                db.close()
            except Exception as e:
                print(f"Error logging site visit: {e}")

        return response