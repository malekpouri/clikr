import geoip2.database
import os
from user_agents import parse
from typing import Dict, Any, Optional

# مسیر فایل دیتابیس GeoLite2
GEOIP_DB_PATH = os.path.join(os.path.dirname(__file__), 'static/GeoLite2-City.mmdb')


def get_geo_info(ip_address: str) -> Dict[str, Any]:
    """استخراج اطلاعات جغرافیایی از آدرس IP"""
    result = {
        'country': None,
        'city': None
    }

    if not ip_address or ip_address == '127.0.0.1' or ip_address.startswith('192.168.'):
        result['country'] = 'Local'
        result['city'] = 'Local'
        return result

    try:
        # اگر فایل دیتابیس GeoIP وجود داشته باشد
        if os.path.exists(GEOIP_DB_PATH):
            with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
                response = reader.city(ip_address)
                result['country'] = response.country.name or response.registered_country.name
                result['city'] = response.city.name
        else:
            # حالت پیش‌فرض اگر دیتابیس وجود نداشت
            result['country'] = 'Unknown'
            result['city'] = 'Unknown'
    except Exception as e:
        # در صورت خطا
        print(f"Error getting geo info: {e}")
        result['country'] = 'Error'
        result['city'] = 'Error'

    return result


def parse_user_agent(user_agent_string: str) -> Dict[str, str]:
    """استخراج اطلاعات دستگاه، مرورگر و سیستم‌عامل از User-Agent"""
    result = {
        'device_type': 'Unknown',
        'browser': 'Unknown',
        'os': 'Unknown'
    }

    if not user_agent_string:
        return result

    try:
        user_agent = parse(user_agent_string)

        # نوع دستگاه
        if user_agent.is_mobile:
            result['device_type'] = 'Mobile'
        elif user_agent.is_tablet:
            result['device_type'] = 'Tablet'
        elif user_agent.is_pc:
            result['device_type'] = 'Desktop'
        elif user_agent.is_bot:
            result['device_type'] = 'Bot'

        # مرورگر
        browser_family = user_agent.browser.family
        browser_version = '.'.join([str(v) for v in user_agent.browser.version if v])
        if browser_version:
            result['browser'] = f"{browser_family} {browser_version}"
        else:
            result['browser'] = browser_family

        # سیستم‌عامل
        os_family = user_agent.os.family
        os_version = '.'.join([str(v) for v in user_agent.os.version if v])
        if os_version:
            result['os'] = f"{os_family} {os_version}"
        else:
            result['os'] = os_family

    except Exception as e:
        print(f"Error parsing user agent: {e}")

    return result


def parse_referer(referer: Optional[str]) -> Optional[str]:
    """استخراج دامنه اصلی از Referer"""
    if not referer:
        return None

    try:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        return parsed.netloc or parsed.path
    except:
        return referer