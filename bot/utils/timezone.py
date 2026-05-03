"""
Timezone konversiya — UTC → foydalanuvchi vaqti.
"""
from datetime import datetime, date, timezone as tz
import pytz
from typing import Optional


def now_in_tz(timezone_str: str) -> datetime:
    """Hozirgi vaqt — berilgan timezone'da."""
    tz_obj = pytz.timezone(timezone_str)
    return datetime.now(tz_obj)


def utc_to_local(dt: datetime, timezone_str: str) -> datetime:
    """UTC vaqtni foydalanuvchi vaqtiga convert qilish."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.utc)
    tz_obj = pytz.timezone(timezone_str)
    return dt.astimezone(tz_obj)


def local_to_utc(dt: datetime, timezone_str: str) -> datetime:
    """Foydalanuvchi vaqtini UTC ga convert qilish."""
    tz_obj = pytz.timezone(timezone_str)
    if dt.tzinfo is None:
        dt = tz_obj.localize(dt)
    return dt.astimezone(pytz.utc)


def format_datetime_for_user(
    dt: datetime,
    timezone_str: str,
    lang: str = "uz"
) -> str:
    """
    Foydalanuvchiga ko'rsatish uchun formatlash.
    "15 May 2026, soat 09:30" yoki "15 Мая 2026, в 09:30"
    """
    local_dt = utc_to_local(dt, timezone_str)

    months_uz = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
        9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
    }
    months_ru = {
        1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля",
        5: "Мая", 6: "Июня", 7: "Июля", 8: "Августа",
        9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"
    }
    months = months_uz if lang == "uz" else months_ru
    month_name = months[local_dt.month]
    time_str = local_dt.strftime("%H:%M")

    if lang == "uz":
        return f"{local_dt.day} {month_name} {local_dt.year}, soat {time_str}"
    else:
        return f"{local_dt.day} {month_name} {local_dt.year}, в {time_str}"
