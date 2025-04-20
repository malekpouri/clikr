import jdatetime
from datetime import datetime


def gregorian_to_jalali(date_obj: datetime) -> str:
    """تبدیل تاریخ میلادی به شمسی با فرمت زیبا"""
    if not date_obj:
        return "بدون تاریخ"

    jdate = jdatetime.datetime.fromgregorian(datetime=date_obj)
    # فرمت: ۱۴۰۴/۰۲/۰۱ ۱۴:۳۰:۰۰
    return jdate.strftime("%Y/%m/%d %H:%M:%S")


def format_remaining_days(date_obj: datetime) -> str:
    """محاسبه تعداد روزهای باقیمانده تا تاریخ انقضا"""
    if not date_obj:
        return "بدون تاریخ انقضا"

    now = datetime.now()

    # اگر تاریخ انقضا گذشته باشد
    if date_obj < now:
        return "منقضی شده"

    # محاسبه تعداد روزهای باقیمانده
    remaining_days = (date_obj - now).days
    remaining_hours = ((date_obj - now).seconds // 3600)

    if remaining_days > 0:
        return f"{remaining_days} روز دیگر"
    elif remaining_hours > 0:
        return f"{remaining_hours} ساعت دیگر"
    else:
        return "کمتر از یک ساعت"