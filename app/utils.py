import re
from nanoid import generate

# تابع بررسی اعتبار URL
def is_valid_url(url: str) -> bool:
    # الگوی ساده برای تشخیص URL معتبر
    pattern = re.compile(
        r'^(https?://)?(www\.)?'  # http:// یا https:// و www (اختیاری)
        r'([a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)'  # دامنه
        r'(:\d+)?'  # پورت (اختیاری)
        r'(/[-a-zA-Z0-9()@:%_\+.~#?&//=]*)?$'  # مسیر (اختیاری)
    )
    return bool(pattern.match(url))

# تابع تولید کد کوتاه تصادفی
def generate_short_code(length: int = 6) -> str:
    # استفاده از کتابخانه nanoid برای تولید کد کوتاه تصادفی
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    return generate(alphabet, length)

# تابع اضافه کردن پروتکل به URL اگر نداشته باشد
def normalize_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url