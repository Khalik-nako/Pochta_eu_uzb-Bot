"""
All inline keyboards in one place.
Each function returns a ready-to-use InlineKeyboardMarkup.
"""
from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import COUNTRY_FLAGS, COUNTRY_TIMEZONES
from locales import t


# ─── ONBOARDING ──────────────────────────────────────────────

def lang_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbek", callback_data="lang:uz")
    kb.button(text="🇷🇺 Русский", callback_data="lang:ru")
    kb.adjust(2)
    return kb.as_markup()


def country_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for country in COUNTRY_TIMEZONES:
        flag = COUNTRY_FLAGS.get(country, "🌍")
        kb.button(text=f"{flag} {country}", callback_data=f"country:{country}")
    kb.adjust(3)
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    kb.button(text=back, callback_data="back:start")
    return kb.as_markup()


def legal_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    text = "✅ Tushundim, davom etaman" if lang == "uz" else "✅ Понятно, продолжаем"
    kb.button(text=text, callback_data="legal:accept")
    return kb.as_markup()


# ─── MAIN MENU ───────────────────────────────────────────────

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="📦 Pochta beraman", callback_data="menu:sender")
        kb.button(text="✈️ Kuryer bo'laman", callback_data="menu:courier")
        kb.button(text="🚕 Taxi — Yevropa bo'ylab", callback_data="menu:taxi")
        kb.button(text="📋 Mening e'lonlarim", callback_data="menu:listings")
        kb.button(text="⭐ Reytingim", callback_data="menu:rating")
        kb.button(text="🚫 Nima olib o'tib bo'lmaydi?", callback_data="menu:airport_rules")
        kb.button(text="🚨 Shikoyat", callback_data="menu:complaint")
        kb.button(text="❓ Yordam", callback_data="menu:help")
        kb.button(text="⚙️ Sozlamalar", callback_data="menu:settings")
    else:
        kb.button(text="📦 Отправить посылку", callback_data="menu:sender")
        kb.button(text="✈️ Стать курьером", callback_data="menu:courier")
        kb.button(text="🚕 Такси — по Европе", callback_data="menu:taxi")
        kb.button(text="📋 Мои объявления", callback_data="menu:listings")
        kb.button(text="⭐ Мой рейтинг", callback_data="menu:rating")
        kb.button(text="🚫 Что нельзя провозить?", callback_data="menu:airport_rules")
        kb.button(text="🚨 Жалоба", callback_data="menu:complaint")
        kb.button(text="❓ Помощь", callback_data="menu:help")
        kb.button(text="⚙️ Настройки", callback_data="menu:settings")
    kb.adjust(1, 1, 1, 2, 1, 2, 1, 1)
    return kb.as_markup()


def back_to_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    text = "🏠 Bosh menyu" if lang == "uz" else "🏠 Главное меню"
    kb.button(text=text, callback_data="back:main")
    return kb.as_markup()


def nav_keyboard(lang: str, back: str = "back:main") -> InlineKeyboardMarkup:
    """Standard back + home navigation."""
    kb = InlineKeyboardBuilder()
    back_text = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    menu_text = "🏠 Bosh menyu" if lang == "uz" else "🏠 Главное меню"
    kb.button(text=back_text, callback_data=back)
    kb.button(text=menu_text, callback_data="back:main")
    kb.adjust(2)
    return kb.as_markup()


# ─── SENDER FLOW ─────────────────────────────────────────────

def month_keyboard(lang: str, months: list) -> InlineKeyboardMarkup:
    """[(display_text, value), ...] — pick departure month."""
    kb = InlineKeyboardBuilder()
    for display, value in months:
        kb.button(text=display, callback_data=f"month:{value}")
    kb.adjust(2)
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    menu = "🏠 Bosh menyu" if lang == "uz" else "🏠 Главное меню"
    kb.button(text=back, callback_data="back:sender_location")
    kb.button(text=menu, callback_data="back:main")
    kb.adjust(2, 2)
    return kb.as_markup()


def courier_sort_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="⚡ Eng yaqin sana", callback_data="sort:date")
        kb.button(text="💰 Eng arzon", callback_data="sort:price")
        kb.button(text="⭐ Eng yuqori reyting", callback_data="sort:rating")
    else:
        kb.button(text="⚡ Ближайшая дата", callback_data="sort:date")
        kb.button(text="💰 Самый дешёвый", callback_data="sort:price")
        kb.button(text="⭐ Высший рейтинг", callback_data="sort:rating")
    kb.adjust(3)
    return kb.as_markup()


def courier_card_keyboard(lang: str, listing_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="👁 Batafsil", callback_data=f"courier_detail:{listing_id}")
        kb.button(text="✅ Tanlash", callback_data=f"courier_select:{listing_id}")
    else:
        kb.button(text="👁 Подробнее", callback_data=f"courier_detail:{listing_id}")
        kb.button(text="✅ Выбрать", callback_data=f"courier_select:{listing_id}")
    kb.adjust(2)
    return kb.as_markup()


def no_couriers_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="🔔 Ha, xabar ber", callback_data="subscribe:yes")
        kb.button(text="Yo'q, rahmat", callback_data="subscribe:no")
        kb.button(text="⬅️ Oyni o'zgartirish", callback_data="back:sender_month")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="🔔 Да, сообщить", callback_data="subscribe:yes")
        kb.button(text="Нет, спасибо", callback_data="subscribe:no")
        kb.button(text="⬅️ Сменить месяц", callback_data="back:sender_month")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(2, 2)
    return kb.as_markup()


def confirm_request_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="✅ Ha, yuboraman", callback_data="request:confirm")
        kb.button(text="❌ Bekor qilish", callback_data="request:cancel")
    else:
        kb.button(text="✅ Да, отправить", callback_data="request:confirm")
        kb.button(text="❌ Отмена", callback_data="request:cancel")
    kb.adjust(2)
    return kb.as_markup()


# ─── COURIER FLOW ────────────────────────────────────────────

def courier_departure_city_keyboard(lang: str, cities: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for city in cities:
        kb.button(text=f"✈️ {city}", callback_data=f"depcity:{city}")
    other = "+ Boshqa shahar" if lang == "uz" else "+ Другой город"
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    kb.button(text=other, callback_data="depcity:other")
    kb.button(text=back, callback_data="back:courier_phone")
    cols = 2 if len(cities) > 1 else 1
    city_rows = [cols] * ((len(cities) + cols - 1) // cols)
    kb.adjust(*city_rows, 1, 1)
    return kb.as_markup()


def restrictions_keyboard(lang: str, selected: list) -> InlineKeyboardMarkup:
    options = [
        ("💊", "Dori-darmon" if lang == "uz" else "Лекарства", "dori"),
        ("💧", "Suyuqlik" if lang == "uz" else "Жидкости", "suyuq"),
        ("📦", "Katta hajm" if lang == "uz" else "Большой объём", "katta"),
        ("🔋", "Batareya" if lang == "uz" else "Батарея", "batareya"),
    ]
    kb = InlineKeyboardBuilder()
    for emoji, label, key in options:
        check = "✅ " if key in selected else ""
        kb.button(text=f"{check}{emoji} {label}", callback_data=f"restrict:{key}")
    custom = "✏️ Boshqa" if lang == "uz" else "✏️ Другое"
    next_btn = "➡️ Davom etish" if lang == "uz" else "➡️ Продолжить"
    kb.button(text=custom, callback_data="restrict:custom")
    kb.button(text=next_btn, callback_data="restrict:done")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


# ─── DEAL FLOW ───────────────────────────────────────────────

def deal_request_keyboard(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="✅ Qabul qilaman", callback_data=f"deal_accept:{deal_id}")
        kb.button(text="❌ Rad etaman", callback_data=f"deal_reject:{deal_id}")
    else:
        kb.button(text="✅ Принять", callback_data=f"deal_accept:{deal_id}")
        kb.button(text="❌ Отклонить", callback_data=f"deal_reject:{deal_id}")
    kb.adjust(2)
    return kb.as_markup()


def deal_start_chat_keyboard(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="💬 Chat boshlash", callback_data=f"start_chat:{deal_id}")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="💬 Начать чат", callback_data=f"start_chat:{deal_id}")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(1)
    return kb.as_markup()


def deal_chat_keyboard(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="✅ Kelishdim", callback_data=f"deal_confirm:{deal_id}")
        kb.button(text="❌ Bekor qilish", callback_data=f"deal_cancel:{deal_id}")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="✅ Договорились", callback_data=f"deal_confirm:{deal_id}")
        kb.button(text="❌ Отменить", callback_data=f"deal_cancel:{deal_id}")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(2, 1)
    return kb.as_markup()


def delivery_confirm_keyboard(lang: str, deal_id: int, is_sender: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_sender:
        if lang == "uz":
            kb.button(text="✅ Ha, oldim va to'ladim", callback_data=f"delivery_confirm:{deal_id}:sender")
            kb.button(text="🚨 Muammo bor", callback_data=f"delivery_problem:{deal_id}")
        else:
            kb.button(text="✅ Да, получил и оплатил", callback_data=f"delivery_confirm:{deal_id}:sender")
            kb.button(text="🚨 Есть проблема", callback_data=f"delivery_problem:{deal_id}")
    else:
        text = "✅ Ha, yetkazdim" if lang == "uz" else "✅ Да, доставил"
        kb.button(text=text, callback_data=f"delivery_confirm:{deal_id}:courier")
    kb.adjust(1)
    return kb.as_markup()


def rating_keyboard(lang: str, deal_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(1, 6):
        kb.button(text="⭐" * i, callback_data=f"rate:{deal_id}:{i}")
    kb.adjust(5)
    return kb.as_markup()


# ─── PROFILE / SETTINGS ──────────────────────────────────────

def listings_filter_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="✅ Faol", callback_data="listings:active")
        kb.button(text="🏁 Tugallangan", callback_data="listings:completed")
        kb.button(text="❌ Bekor qilingan", callback_data="listings:cancelled")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="✅ Активные", callback_data="listings:active")
        kb.button(text="🏁 Завершённые", callback_data="listings:completed")
        kb.button(text="❌ Отменённые", callback_data="listings:cancelled")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(3, 1)
    return kb.as_markup()


def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="🌐 Tilni o'zgartirish", callback_data="settings:lang")
        kb.button(text="🌍 Davlatni o'zgartirish", callback_data="settings:country")
        kb.button(text="📞 Telefon o'zgartirish", callback_data="settings:phone")
        kb.button(text="🗑 Akkauntni o'chirish", callback_data="settings:delete")
        kb.button(text="⬅️ Orqaga", callback_data="back:main")
    else:
        kb.button(text="🌐 Изменить язык", callback_data="settings:lang")
        kb.button(text="🌍 Изменить страну", callback_data="settings:country")
        kb.button(text="📞 Изменить телефон", callback_data="settings:phone")
        kb.button(text="🗑 Удалить аккаунт", callback_data="settings:delete")
        kb.button(text="⬅️ Назад", callback_data="back:main")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def complaint_reason_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        reasons = [
            ("📦 Yuk yetmadi", "not_delivered"),
            ("💸 Aldov / Scam", "scam"),
            ("🤐 Muloqot yo'q", "no_contact"),
            ("📋 Boshqa", "other"),
        ]
    else:
        reasons = [
            ("📦 Груз не дошёл", "not_delivered"),
            ("💸 Мошенничество", "scam"),
            ("🤐 Нет связи", "no_contact"),
            ("📋 Другое", "other"),
        ]
    for text, key in reasons:
        kb.button(text=text, callback_data=f"complaint_reason:{key}")
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    kb.button(text=back, callback_data="back:main")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def airport_rules_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="🎒 Qo'l yukiga nima olish mumkin?", callback_data="airport:carry_on")
        kb.button(text="🧳 Bagajga nima olish mumkin?", callback_data="airport:baggage")
        kb.button(text="🚫 Mutlaqo olib bo'lmaydigan narsalar", callback_data="airport:forbidden")
        kb.button(text="💡 Foydali maslahatlar", callback_data="airport:tips")
        kb.button(text="⬅️ Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="🎒 Что можно в ручную кладь?", callback_data="airport:carry_on")
        kb.button(text="🧳 Что можно в багаж?", callback_data="airport:baggage")
        kb.button(text="🚫 Абсолютно запрещённые предметы", callback_data="airport:forbidden")
        kb.button(text="💡 Полезные советы", callback_data="airport:tips")
        kb.button(text="⬅️ Главное меню", callback_data="back:main")
    kb.adjust(1)
    return kb.as_markup()


def admin_contact_keyboard(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    text = "📩 Adminga yozish" if lang == "uz" else "📩 Написать администратору"
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    kb.button(text=text, url="https://t.me/pochta_admin")
    kb.button(text=back, callback_data="back:main")
    kb.adjust(1)
    return kb.as_markup()


# ─── ADMIN KEYBOARDS ─────────────────────────────────────────

def admin_main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Kuryer tasdiqlash", callback_data="admin:verify")
    kb.button(text="📋 Faol e'lonlar", callback_data="admin:listings")
    kb.button(text="🚨 Shikoyatlar", callback_data="admin:complaints")
    kb.button(text="🚫 Bloklash", callback_data="admin:block")
    kb.button(text="📊 Statistika", callback_data="admin:stats")
    kb.button(text="📣 Xabar yuborish", callback_data="admin:broadcast")
    kb.button(text="🚕 Taxi boshqarish", callback_data="admin:taxi")
    kb.button(text="🔄 Yangilash", callback_data="admin:main")
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup()


def admin_verify_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Videoni ko'rish", callback_data=f"admin_video:{listing_id}")
    kb.button(text="✅ Tasdiqlash", callback_data=f"admin_approve:{listing_id}")
    kb.button(text="❌ Rad etish", callback_data=f"admin_reject:{listing_id}")
    kb.button(text="🔄 Qayta video so'rash", callback_data=f"admin_revideo:{listing_id}")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def admin_reject_reason_keyboard(listing_id: int) -> InlineKeyboardMarkup:
    reasons = [
        ("😶 Yuz aniq emas", "face"),
        ("📄 Pasport ko'rinmaydi", "passport"),
        ("🔤 Ism mos emas", "name"),
        ("🎥 Video sifatsiz", "quality"),
        ("🔞 18 yoshdan kichik", "age"),
    ]
    kb = InlineKeyboardBuilder()
    for text, key in reasons:
        kb.button(text=text, callback_data=f"reject_reason:{listing_id}:{key}")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def admin_complaint_keyboard(complaint_id: int, against_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Ikkalasiga yozish", callback_data=f"admin_chat:{complaint_id}")
    kb.button(text="✅ Hal qilindi", callback_data=f"complaint_resolve:{complaint_id}")
    kb.button(text="🚫 Bloklash", callback_data=f"admin_block:{against_id}")
    kb.button(text="📁 Arxivlash", callback_data=f"complaint_archive:{complaint_id}")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Admin xabar yuborish — barcha davlatlar dinamik."""
    from config import COUNTRY_TIMEZONES, COUNTRY_FLAGS
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Barcha foydalanuvchilar", callback_data="broadcast:all")
    kb.button(text="✈️ Faqat kuryrlar", callback_data="broadcast:couriers")
    kb.button(text="📦 Faqat jo'natuvchilar", callback_data="broadcast:senders")
    # Har bir davlat uchun alohida tugma
    for country in list(COUNTRY_TIMEZONES.keys())[:10]:  # Max 10 ta davlat ko'rsatiladi
        flag = COUNTRY_FLAGS.get(country, "🌍")
        kb.button(text=f"{flag} {country}", callback_data=f"broadcast:country:{country}")
    kb.button(text="🌍 Boshqa davlatlar...", callback_data="broadcast:more_countries")
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    kb.adjust(1, 2, 2, 2, 2, 2, 1)
    return kb.as_markup()


def admin_broadcast_countries_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Barcha davlatlar ro'yxati — sahifalab."""
    from config import COUNTRY_TIMEZONES, COUNTRY_FLAGS
    countries = list(COUNTRY_TIMEZONES.keys())
    per_page = 8
    start = page * per_page
    chunk = countries[start:start + per_page]

    kb = InlineKeyboardBuilder()
    for country in chunk:
        flag = COUNTRY_FLAGS.get(country, "🌍")
        kb.button(text=f"{flag} {country}", callback_data=f"broadcast:country:{country}")
    kb.adjust(2)

    nav = []
    if page > 0:
        kb.button(text="◀️ Oldingi", callback_data=f"broadcast:countries_page:{page - 1}")
        nav.append(1)
    if start + per_page < len(countries):
        kb.button(text="Keyingi ▶️", callback_data=f"broadcast:countries_page:{page + 1}")
        nav.append(1)
    if nav:
        kb.adjust(2, *([2] * (len(chunk) // 2)), len(nav))
    kb.button(text="⬅️ Orqaga", callback_data="admin:broadcast")
    return kb.as_markup()


# ─── TAXI KEYBOARDS ───────────────────────────────────────────

def taxi_list_keyboard(lang: str, taxis: list) -> InlineKeyboardMarkup:
    """Taxi xizmatlari ro'yxati."""
    kb = InlineKeyboardBuilder()
    for taxi in taxis:
        pin_icon = "📌 " if taxi.is_pinned else ""
        countries_short = taxi.countries[:30] + "..." if len(taxi.countries) > 30 else taxi.countries
        driver_name = taxi.driver.full_name.split()[0] if taxi.driver else "—"
        kb.button(
            text=f"{pin_icon}🚕 {driver_name} · {countries_short}",
            callback_data=f"taxi:view:{taxi.id}"
        )
    if lang == "uz":
        kb.button(text="✍️ Men taxi boshqaruvchisiman", callback_data="taxi:register_driver")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="✍️ Я таксист / водитель", callback_data="taxi:register_driver")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(1)
    return kb.as_markup()


def taxi_detail_keyboard(lang: str, taxi_id: int) -> InlineKeyboardMarkup:
    """Taxi tafsiloti."""
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="📩 Adminga yozish / Bog'lanish", callback_data=f"taxi:contact:{taxi_id}")
        kb.button(text="⬅️ Orqaga", callback_data="menu:taxi")
    else:
        kb.button(text="📩 Написать администратору", callback_data=f"taxi:contact:{taxi_id}")
        kb.button(text="⬅️ Назад", callback_data="menu:taxi")
    kb.adjust(1)
    return kb.as_markup()


def taxi_driver_register_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Taxi haydovchi so'rovi uchun."""
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="✅ Ha, so'rov yuboraman", callback_data="taxi:send_request")
        kb.button(text="❌ Bekor qilish", callback_data="menu:taxi")
    else:
        kb.button(text="✅ Да, отправить заявку", callback_data="taxi:send_request")
        kb.button(text="❌ Отмена", callback_data="menu:taxi")
    kb.adjust(1)
    return kb.as_markup()


def admin_taxi_keyboard(taxi_id: int) -> InlineKeyboardMarkup:
    """Admin — taxi boshqarish."""
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Tahrirlash", callback_data=f"admin_taxi:edit:{taxi_id}")
    kb.button(text="📌 Pinlash / Olib tashlash", callback_data=f"admin_taxi:pin:{taxi_id}")
    kb.button(text="🗑 O'chirish", callback_data=f"admin_taxi:delete:{taxi_id}")
    kb.button(text="⬅️ Orqaga", callback_data="admin:taxi")
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def admin_taxi_list_keyboard(taxis: list) -> InlineKeyboardMarkup:
    """Admin — barcha taxi xizmatlari."""
    kb = InlineKeyboardBuilder()
    for taxi in taxis:
        pin_icon = "📌 " if taxi.is_pinned else ""
        driver_name = taxi.driver.full_name.split()[0] if taxi.driver else "—"
        kb.button(
            text=f"{pin_icon}🚕 #{taxi.id} {driver_name}",
            callback_data=f"admin_taxi:manage:{taxi.id}"
        )
    kb.button(text="➕ Yangi taxi qo'shish", callback_data="admin_taxi:add")
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    kb.adjust(1)
    return kb.as_markup()


# ─── ADMIN LISTING MANAGEMENT ────────────────────────────────

def admin_listing_manage_keyboard(listing_id: int, is_pinned: bool = False) -> InlineKeyboardMarkup:
    """Admin — faol e'lonni boshqarish."""
    kb = InlineKeyboardBuilder()
    pin_text = "📌 Pindan olib tashlash" if is_pinned else "📌 Tepaga pinlash"
    kb.button(text="✏️ Tahrirlash (narx/kg)", callback_data=f"admin_listing:edit:{listing_id}")
    kb.button(text=pin_text, callback_data=f"admin_listing:pin:{listing_id}")
    kb.button(text="💎 Diamond stikker berish", callback_data=f"admin_listing:diamond:{listing_id}")
    kb.button(text="🗑 E'lonni o'chirish", callback_data=f"admin_listing:delete:{listing_id}")
    kb.button(text="⬅️ Orqaga", callback_data="admin:listings")
    kb.adjust(2, 2, 1)
    return kb.as_markup()

