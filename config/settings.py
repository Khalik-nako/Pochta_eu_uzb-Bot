"""
Loyiha konfiguratsiyasi — barcha sozlamalar shu yerda.
"""
from dataclasses import dataclass, field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str
    username: str
    admin_ids: List[int]


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class RedisConfig:
    url: str


@dataclass
class ChannelConfig:
    video_channel_id: int


@dataclass
class WebhookConfig:
    url: str
    path: str
    port: int


@dataclass
class AppConfig:
    bot: BotConfig
    db: DatabaseConfig
    redis: RedisConfig
    channel: ChannelConfig
    webhook: WebhookConfig
    run_mode: str
    log_level: str


def _parse_admin_ids(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def load_config() -> AppConfig:
    return AppConfig(
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN", ""),
            username=os.getenv("BOT_USERNAME", "pochta_bot"),
            admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        ),
        db=DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pochta.db"),
        ),
        redis=RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ),
        channel=ChannelConfig(
            video_channel_id=int(os.getenv("VIDEO_CHANNEL_ID", "0")),
        ),
        webhook=WebhookConfig(
            url=os.getenv("WEBHOOK_URL", ""),
            path=os.getenv("WEBHOOK_PATH", "/webhook"),
            port=int(os.getenv("WEBHOOK_PORT", "8080")),
        ),
        run_mode=os.getenv("RUN_MODE", "polling"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Global config instance
config = load_config()

# Qo'llab-quvvatlangan davlatlar va timezone xaritasi
COUNTRY_TIMEZONES = {
    "Latviya":        "Europe/Riga",
    "Litva":          "Europe/Vilnius",
    "Estoniya":       "Europe/Tallinn",
    "Germaniya":      "Europe/Berlin",
    "Polsha":         "Europe/Warsaw",
    "Chexiya":        "Europe/Prague",
    "Slovakiya":      "Europe/Bratislava",
    "Vengriya":       "Europe/Budapest",
    "Avstriya":       "Europe/Vienna",
    "Belgiya":        "Europe/Brussels",
    "Niderlandiya":   "Europe/Amsterdam",
    "Fransiya":       "Europe/Paris",
    "Ispaniya":       "Europe/Madrid",
    "Italiya":        "Europe/Rome",
    "Portugaliya":    "Europe/Lisbon",
    "Britaniya":      "Europe/London",
    "Irlandiya":      "Europe/Dublin",
    "Shvetsiya":      "Europe/Stockholm",
    "Norvegiya":      "Europe/Oslo",
    "Daniya":         "Europe/Copenhagen",
    "Finlandiya":     "Europe/Helsinki",
    "Shveytsariya":   "Europe/Zurich",
    "Ruminiya":       "Europe/Bucharest",
    "Bolgariya":      "Europe/Sofia",
    "Gretsiya":       "Europe/Athens",
    "Serbiya":        "Europe/Belgrade",
    "Xorvatiya":      "Europe/Zagreb",
    "Sloveniya":      "Europe/Ljubljana",
    "Ukraina":        "Europe/Kyiv",
}

# Davlatlar uchun bayroq emoji
COUNTRY_FLAGS = {
    "Latviya": "🇱🇻",    "Germaniya": "🇩🇪",   "Polsha": "🇵🇱",
    "Britaniya": "🇬🇧",  "Fransiya": "🇫🇷",    "Italiya": "🇮🇹",
    "Ispaniya": "🇪🇸",   "Niderlandiya": "🇳🇱", "Belgiya": "🇧🇪",
    "Avstriya": "🇦🇹",   "Shveytsariya": "🇨🇭", "Shvetsiya": "🇸🇪",
    "Norvegiya": "🇳🇴",  "Daniya": "🇩🇰",      "Finlandiya": "🇫🇮",
    "Portugaliya": "🇵🇹","Irlandiya": "🇮🇪",   "Chexiya": "🇨🇿",
    "Slovakiya": "🇸🇰",  "Vengriya": "🇭🇺",    "Ruminiya": "🇷🇴",
    "Bolgariya": "🇧🇬",  "Gretsiya": "🇬🇷",    "Serbiya": "🇷🇸",
    "Xorvatiya": "🇭🇷",  "Sloveniya": "🇸🇮",   "Ukraina": "🇺🇦",
    "Litva": "🇱🇹",      "Estoniya": "🇪🇪",
}

# Yo'nalish shaharlari — har davlat uchun bir nechta shahar
DEPARTURE_CITIES: dict[str, list[str]] = {
    "Latviya":      ["Riga"],
    "Litva":        ["Vilnyus"],
    "Estoniya":     ["Tallin"],
    "Germaniya":    ["Frankfurt", "Myunxen", "Berlin", "Dyusseldorf", "Gamburg", "Shtutgart"],
    "Polsha":       ["Varshava", "Krakov", "Vrotslav", "Gdansk", "Poznon"],
    "Britaniya":    ["London Heathrow", "London Gatwick", "Manchester", "Birmingham"],
    "Fransiya":     ["Parij CDG", "Parij Orly", "Lion", "Marsel"],
    "Italiya":      ["Rim", "Milan", "Venetsiya", "Florentsiya", "Neapol"],
    "Ispaniya":     ["Madrid", "Barselona", "Valensiya", "Sevil"],
    "Niderlandiya": ["Amsterdam"],
    "Belgiya":      ["Bryussel", "Antverpen"],
    "Avstriya":     ["Vena"],
    "Shveytsariya": ["Syurih", "Jeneva", "Bazel"],
    "Shvetsiya":    ["Stokgolm Arlanda", "Gyoteborg"],
    "Norvegiya":    ["Oslo"],
    "Daniya":       ["Kopengagen"],
    "Finlandiya":   ["Xelsinki"],
    "Chexiya":      ["Praga"],
    "Slovakiya":    ["Bratislava"],
    "Vengriya":     ["Budapesht"],
    "Ruminiya":     ["Buxarest"],
    "Bolgariya":    ["Sofiya"],
    "Gretsiya":     ["Afina"],
    "Serbiya":      ["Belgrad"],
    "Xorvatiya":    ["Zagreb"],
    "Sloveniya":    ["Lyublyana"],
    "Ukraina":      ["Kiyev"],
    "Portugaliya":  ["Lissabon", "Porto"],
    "Irlandiya":    ["Dublin"],
}

# Har davlat uchun telefon raqam misoli
COUNTRY_PHONE_EXAMPLES: dict[str, str] = {
    "Latviya":      "+371 2345 6789",
    "Litva":        "+370 612 34567",
    "Estoniya":     "+372 5123 4567",
    "Germaniya":    "+49 151 2345 6789",
    "Polsha":       "+48 512 345 678",
    "Britaniya":    "+44 7911 123456",
    "Fransiya":     "+33 6 12 34 56 78",
    "Italiya":      "+39 312 345 6789",
    "Ispaniya":     "+34 612 345 678",
    "Niderlandiya": "+31 6 12345678",
    "Belgiya":      "+32 471 12 34 56",
    "Avstriya":     "+43 650 1234567",
    "Shveytsariya": "+41 78 123 45 67",
    "Shvetsiya":    "+46 70 123 45 67",
    "Norvegiya":    "+47 412 34 567",
    "Daniya":       "+45 20 12 34 56",
    "Finlandiya":   "+358 40 1234567",
    "Chexiya":      "+420 601 234 567",
    "Slovakiya":    "+421 901 234 567",
    "Vengriya":     "+36 20 123 4567",
    "Ruminiya":     "+40 721 234 567",
    "Bolgariya":    "+359 87 123 4567",
    "Gretsiya":     "+30 69 1234 5678",
    "Serbiya":      "+381 60 1234567",
    "Xorvatiya":    "+385 91 234 5678",
    "Sloveniya":    "+386 40 123 456",
    "Ukraina":      "+380 50 123 4567",
    "Portugaliya":  "+351 912 345 678",
    "Irlandiya":    "+353 85 123 4567",
}
