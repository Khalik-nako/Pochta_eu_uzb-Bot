"""
Til tizimi testlari.
"""
import pytest
from locales import t, get_messages


class TestLocales:
    def test_uz_main_menu(self):
        result = t("uz", "MAIN_MENU")
        assert result  # bo'sh emas

    def test_ru_main_menu(self):
        result = t("ru", "MAIN_MENU")
        assert result

    def test_uz_and_ru_different(self):
        uz = t("uz", "MAIN_MENU")
        ru = t("ru", "MAIN_MENU")
        assert uz != ru

    def test_format_with_kwargs(self):
        result = t("uz", "REQUEST_SENT",
                   courier_name="Alisher", city="Riga", date="15.05.2026")
        assert "Alisher" in result
        assert "Riga" in result

    def test_missing_key_returns_placeholder(self):
        result = t("uz", "NONEXISTENT_KEY_XYZ")
        assert "NONEXISTENT_KEY_XYZ" in result

    def test_unknown_lang_defaults_to_uz(self):
        result = t("fr", "MAIN_MENU")
        uz_result = t("uz", "MAIN_MENU")
        assert result == uz_result
