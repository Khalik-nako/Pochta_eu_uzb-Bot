"""
Validatorlar — sana, vaqt, telefon tekshiruvlari.
"""
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import phonenumbers


# ─── SANA VALIDATOR ──────────────────────────

def validate_date(text: str) -> Optional[date]:
    """
    "15.05.2026" formatdagi sanani tekshiradi.
    To'g'ri bo'lsa date qaytaradi, xato bo'lsa None.
    """
    text = text.strip()
    pattern = r"^(\d{2})\.(\d{2})\.(\d{4})$"
    match = re.match(pattern, text)
    if not match:
        return None
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        parsed = date(year, month, day)
        # O'tgan sanani qabul qilmaymiz
        if parsed < date.today():
            return None
        return parsed
    except ValueError:
        return None


# ─── VAQT VALIDATOR ──────────────────────────

def validate_time(text: str) -> Optional[str]:
    """
    "09:30" formatdagi vaqtni tekshiradi.
    To'g'ri bo'lsa "HH:MM" qaytaradi, xato bo'lsa None.
    """
    text = text.strip()
    pattern = r"^(\d{1,2}):(\d{2})$"
    match = re.match(pattern, text)
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return f"{hour:02d}:{minute:02d}"


# ─── TELEFON VALIDATOR ────────────────────────

def validate_phone(text: str) -> Optional[str]:
    """
    Telefon raqamini tekshiradi va normallashtiradi.
    "+371 2345 6789" → "+37123456789"
    """
    text = text.strip()
    # Faqat + va raqamlar qoldirish
    cleaned = re.sub(r"[^\d+]", "", text)
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    try:
        parsed = phonenumbers.parse(cleaned, None)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except phonenumbers.NumberParseException:
        pass
    return None


# ─── KG VA NARX VALIDATOR ─────────────────────

def validate_kg(text: str) -> Optional[float]:
    """1-100 kg oralig'ini tekshiradi."""
    try:
        value = float(text.strip().replace(",", "."))
        if 0.1 <= value <= 100:
            return value
    except ValueError:
        pass
    return None


def validate_price(text: str) -> Optional[float]:
    """0.1-100 € oralig'idagi narxni tekshiradi."""
    try:
        value = float(text.strip().replace(",", "."))
        if 0.1 <= value <= 100:
            return value
    except ValueError:
        pass
    return None


# ─── ISM VALIDATOR ───────────────────────────

def validate_fullname(text: str) -> Optional[str]:
    """Ism familya: kamida 2 so'z, har biri kamida 2 harf, faqat harf/defis."""
    import unicodedata
    text = text.strip()
    if len(text) < 4 or len(text) > 100:
        return None
    parts = text.split()
    if len(parts) < 2:
        return None
    # Har bir qism kamida 2 harf bo'lishi kerak
    for part in parts:
        # Faqat harflar va defis ruxsat etiladi
        cleaned = part.replace("-", "")
        if len(cleaned) < 2:
            return None
        # Hech bo'lmasa bitta harf bo'lishi kerak (lotin yoki kirill)
        has_letter = any(unicodedata.category(c).startswith("L") for c in cleaned)
        if not has_letter:
            return None
        # Faqat harf va defisdan iborat bo'lishi kerak
        if not all(unicodedata.category(c).startswith("L") or c == "-" for c in cleaned):
            return None
    return " ".join(p.capitalize() for p in parts)


# ─── DISPLAY HELPERS ─────────────────────────

def format_date_display(d: date, lang: str = "uz") -> str:
    """date → "15 May 2026" (ko'rsatish uchun)"""
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
    return f"{d.day} {months[d.month]} {d.year}"


def format_month_display(year: int, month: int, lang: str = "uz") -> str:
    """Oy ko'rsatish uchun: "May 2026" yoki "Май 2026" """
    months_uz = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
        9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
    }
    months_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    months = months_uz if lang == "uz" else months_ru
    return f"{months[month]} {year}"


def get_available_months(count: int = 6) -> List[Tuple[str, str]]:
    """
    Hozirgi oydan boshlab kelgusi oylarni qaytaradi.
    [("May 2026", "2026-05"), ("Iyun 2026", "2026-06"), ...]
    """
    from calendar import monthrange
    result = []
    today = date.today()
    year, month = today.year, today.month
    for _ in range(count):
        display = format_month_display(year, month)
        value = f"{year}-{month:02d}"
        result.append((display, value))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result
