#!/bin/bash

# شروع cron در پس‌زمینه
cron

# شروع برنامه اصلی
exec uvicorn app.main:app --host 0.0.0.0 --port 8000