# app/geo_utils.py - برنچ geo_info
import os
import geoip2.database
from user_agents import parse
from typing import Dict, Any, Optional

# مسیر دیتابیس GeoLite2
GEOLITE2_CITY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/GeoLite2-City.mmdb')


def get_geo_info(ip_address: str) -> Dict[str, Any]:
    """استخراج اطلاعات جغرافیایی از آدرس IP"""
    result = {
        'country': None,
        'city': None
    }

    # if not ip_address : #or ip_address in ('127.0.0.1', 'localhost', '::1'):
    #     return result
    if not ip_address or ip_address == '127.0.0.1' or ip_address.startswith(('192.168.', '10.', '172.16.', '::1')):
        result['country'] = 'Local Network'
        result['city'] = 'Local'
        return result

    try:
        if os.path.exists(GEOLITE2_CITY_PATH):
            with geoip2.database.Reader(GEOLITE2_CITY_PATH) as reader:
                response = reader.city(ip_address)
                result['country'] = response.country.name
                result['city'] = response.city.name
        else:
            # حالت پیش‌فرض اگر دیتابیس وجود نداشت
            result['country'] = 'Unknown'
            result['city'] = 'Unknown'
    except Exception as e:
        print(f"خطا در استخراج اطلاعات جغرافیایی: {e}")
        result['country'] = 'Error'
        result['city'] = 'Error'

    return result


def parse_user_agent(user_agent_string: Optional[str]) -> Dict[str, Any]:
    """استخراج اطلاعات دستگاه از User-Agent"""
    result = {
        'device_type': None,
        'browser': None,
        'os': None
    }

    if not user_agent_string:
        return result

    try:
        user_agent = parse(user_agent_string)

        # تشخیص نوع دستگاه
        if user_agent.is_mobile:
            result['device_type'] = 'موبایل'
        elif user_agent.is_tablet:
            result['device_type'] = 'تبلت'
        elif user_agent.is_pc:
            result['device_type'] = 'کامپیوتر'
        else:
            result['device_type'] = 'ناشناس'

        # تشخیص مرورگر
        result['browser'] = f"{user_agent.browser.family} {user_agent.browser.version_string}"

        # تشخیص سیستم عامل
        result['os'] = f"{user_agent.os.family} {user_agent.os.version_string}"
    except Exception as e:
        print(f"خطا در پردازش User-Agent: {e}")

    return result


def parse_referrer(referrer: Optional[str]) -> Optional[str]:
    """پردازش آدرس ارجاع دهنده"""
    if not referrer:
        return None

    # حذف پارامترهای URL و استخراج دامنه اصلی
    try:
        from urllib.parse import urlparse
        parsed = urlparse(referrer)
        return parsed.netloc or referrer
    except:
        return referrer