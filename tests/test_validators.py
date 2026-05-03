"""
Validator testlari.
Ishlatish: pytest tests/
"""
import pytest
from datetime import date, timedelta

from bot.utils.validators import (
    validate_date, validate_time, validate_phone,
    validate_fullname, validate_kg, validate_price,
    format_date_display,
)


class TestDateValidator:
    def test_valid_date(self):
        tomorrow = date.today() + timedelta(days=1)
        result = validate_date(tomorrow.strftime("%d.%m.%Y"))
        assert result == tomorrow

    def test_past_date_rejected(self):
        yesterday = date.today() - timedelta(days=1)
        assert validate_date(yesterday.strftime("%d.%m.%Y")) is None

    def test_wrong_format(self):
        assert validate_date("2026-05-15") is None
        assert validate_date("15/05/2026") is None
        assert validate_date("abc") is None

    def test_invalid_date(self):
        assert validate_date("32.13.2026") is None

    def test_correct_format(self):
        result = validate_date("15.05.2027")
        assert result == date(2027, 5, 15)


class TestTimeValidator:
    def test_valid_times(self):
        assert validate_time("09:30") == "09:30"
        assert validate_time("00:00") == "00:00"
        assert validate_time("23:59") == "23:59"
        assert validate_time("9:05") == "09:05"

    def test_invalid_times(self):
        assert validate_time("25:00") is None
        assert validate_time("12:60") is None
        assert validate_time("abc") is None
        assert validate_time("9.30") is None


class TestPhoneValidator:
    def test_valid_phones(self):
        assert validate_phone("+37123456789") is not None
        assert validate_phone("+44 7911 123456") is not None

    def test_invalid_phones(self):
        assert validate_phone("abc") is None
        assert validate_phone("123") is None


class TestFullnameValidator:
    def test_valid_names(self):
        assert validate_fullname("Bobur Toshmatov") == "Bobur Toshmatov"
        assert validate_fullname("  Alisher  Karimov  ") == "Alisher  Karimov"

    def test_single_word_rejected(self):
        assert validate_fullname("Bobur") is None

    def test_too_short(self):
        assert validate_fullname("A B") is None  # 3 ta belgi


class TestKgValidator:
    def test_valid(self):
        assert validate_kg("8") == 8.0
        assert validate_kg("0.5") == 0.5
        assert validate_kg("100") == 100.0

    def test_invalid(self):
        assert validate_kg("0") is None
        assert validate_kg("101") is None
        assert validate_kg("abc") is None


class TestFormatDate:
    def test_uz(self):
        result = format_date_display(date(2026, 5, 15), "uz")
        assert "15" in result and "May" in result and "2026" in result

    def test_ru(self):
        result = format_date_display(date(2026, 5, 15), "ru")
        assert "15" in result and "Мая" in result and "2026" in result
