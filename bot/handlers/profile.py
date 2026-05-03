"""
Profil, e'lonlar, reyting, shikoyat, yordam, sozlamalar — S-50..S-54
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from database import get_session, UserRepo, ListingRepo, DealRepo, ComplaintRepo
from database.models import User, ListingStatus, ComplaintStatus
from locales import t
from bot.states.states import ComplaintStates
from bot.keyboards.inline import (
    listings_filter_keyboard, back_to_menu_keyboard, settings_keyboard,
    complaint_reason_keyboard, nav_keyboard, lang_keyboard, country_keyboard,
)

router = Router(name="profile")


# ─── S-50: MENING E'LONLARIM ─────────────────

@router.callback_query(F.data == "menu:listings")
async def my_listings(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    if not user:
        await cb.answer("❌ Avval ro'yxatdan o'ting" if lang == "uz" else "❌ Сначала зарегистрируйтесь", show_alert=True)
        return
    # Pending listinglarni ham ko'rsatish
    async with get_session() as session:
        all_listings = await ListingRepo.get_by_user(session, user.id)
    pending = [l for l in all_listings if l.status.value == "pending"]
    extra = ""
    if pending:
        extra = (
            f"\n\n⏳ <b>Tasdiqlash kutilmoqda: {len(pending)} ta e'lon</b>\n"
            "(Admin tekshirmoqda, 2-12 soat ichida javob beriladi)"
            if lang == "uz" else
            f"\n\n⏳ <b>На проверке: {len(pending)} объявл.</b>\n"
            "(Администратор проверяет, ответ в течение 2-12 ч)"
        )
    title = t(lang, "MY_LISTINGS_TITLE") + extra
    await cb.message.edit_text(
        title,
        reply_markup=listings_filter_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("listings:"))
async def listings_filter(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    filter_key = cb.data.split(":")[1]  # active | completed | cancelled

    status_map = {
        "active": ListingStatus.active,
        "completed": ListingStatus.completed,
        "cancelled": ListingStatus.deleted,
    }
    status = status_map.get(filter_key, ListingStatus.active)

    async with get_session() as session:
        listings = await ListingRepo.get_by_user(session, user.id)

    filtered = [l for l in listings if l.status == status]

    if not filtered:
        empty = (
            "Bu bo'limda e'lonlar yo'q." if lang == "uz"
            else "В этом разделе нет объявлений."
        )
        await cb.answer(empty, show_alert=True)
        return

    lines = []
    for l in filtered[:15]:
        icon = {"active": "✅", "completed": "🏁", "cancelled": "❌"}.get(filter_key, "📋")
        lines.append(
            f"{icon} <b>{l.from_city} → Toshkent</b>\n"
            f"📅 {l.flight_date.strftime('%d.%m.%Y')} · {l.flight_time}\n"
            f"⚖️ {l.max_kg} kg · 💶 €{l.price_per_kg}/kg\n"
            f"🆔 #{l.id}"
        )

    text = "\n\n".join(lines)
    await cb.message.edit_text(
        text,
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-51: REYTINGIM ─────────────────────────

@router.callback_query(F.data == "menu:rating")
async def my_rating(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    rating = round(user.rating, 1) if user and user.rating else 0
    count = user.deal_count if user else 0

    stars = "⭐" * int(rating) if rating else "—"
    text = (
        f"⭐ <b>Sizning reytingiz</b>\n\n"
        f"Baho: {rating}/5  {stars}\n"
        f"Jami deallar: {count}"
        if lang == "uz" else
        f"⭐ <b>Ваш рейтинг</b>\n\n"
        f"Оценка: {rating}/5  {stars}\n"
        f"Всего сделок: {count}"
    )
    await cb.message.edit_text(
        text,
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-52: SHIKOYAT ──────────────────────────

from aiogram.fsm.state import State, StatesGroup

class ComplaintExtStates(StatesGroup):
    enter_against = State()   # Kim haqida
    select_reason = State()
    enter_detail = State()


@router.callback_query(F.data == "menu:complaint")
async def complaint_menu(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    if not user or not user.phone or user.phone.startswith("pending"):
        # Ro'yxatdan o'tmagan — shikoyat qila olmaydi
        not_reg = (
            "⚠️ Shikoyat qilish uchun avval <b>ro'yxatdan o'ting</b>.\n\n"
            "Kuryer yoki jo'natuvchi bo'lib ro'yxatdan o'tgach shikoyat qilishingiz mumkin."
            if lang == "uz" else
            "⚠️ Для подачи жалобы сначала <b>зарегистрируйтесь</b>.\n\n"
            "Станьте курьером или отправителем, затем подавайте жалобу."
        )
        await cb.message.edit_text(not_reg, reply_markup=back_to_menu_keyboard(lang), parse_mode="HTML")
        await cb.answer()
        return

    await state.set_state(ComplaintExtStates.enter_against)
    text = (
        "🚨 <b>Shikoyat</b>\n\n"
        "Kim haqida shikoyat qilmoqchisiz?\n\n"
        "<i>Telegram username (@username) yoki telefon raqamini kiriting</i>"
        if lang == "uz" else
        "🚨 <b>Жалоба</b>\n\n"
        "На кого вы хотите пожаловаться?\n\n"
        "<i>Введите Telegram username (@username) или номер телефона</i>"
    )
    await cb.message.edit_text(text, reply_markup=nav_keyboard(lang, "back:main"), parse_mode="HTML")
    await cb.answer()


@router.message(ComplaintExtStates.enter_against)
async def complaint_against(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    text = (message.text or "").strip()

    if len(text) < 3:
        await message.answer(
            "❌ Kamida 3 belgi kiriting (username yoki telefon)"
            if lang == "uz" else
            "❌ Введите минимум 3 символа (username или телефон)"
        )
        return

    # DB dan qidirish
    against_id = None
    against_name = text
    async with get_session() as session:
        if text.startswith("@"):
            username = text[1:]
            from sqlalchemy import select as sq
            from database.models import User as UserModel
            from sqlalchemy import func as sqfunc
            result = await session.execute(
                sq(UserModel).where(sqfunc.lower(UserModel.full_name).contains(username.lower()))
            )
            found = result.scalar_one_or_none()
            if found:
                against_id = found.id
                against_name = found.full_name
        else:
            from bot.utils.validators import validate_phone
            phone = validate_phone(text)
            if phone:
                found = await UserRepo.get_by_phone(session, phone)
                if found:
                    against_id = found.id
                    against_name = found.full_name

    await state.update_data(
        against_id=against_id,
        against_name=against_name,
        against_raw=text,
    )
    await state.set_state(ComplaintExtStates.select_reason)

    confirm = (
        f"👤 Shikoyat: <b>{against_name}</b>\n\nShikoyat sababini tanlang:"
        if lang == "uz" else
        f"👤 Жалоба на: <b>{against_name}</b>\n\nВыберите причину жалобы:"
    )
    await message.answer(confirm, reply_markup=complaint_reason_keyboard(lang), parse_mode="HTML")


@router.callback_query(ComplaintExtStates.select_reason, F.data.startswith("complaint_reason:"))
async def complaint_reason(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    reason_key = cb.data.split(":")[1]
    await state.update_data(complaint_reason=reason_key)
    await state.set_state(ComplaintExtStates.enter_detail)
    await cb.message.edit_text(
        t(lang, "COMPLAINT_DETAIL"),
        reply_markup=nav_keyboard(lang, "menu:complaint"),
        parse_mode="HTML",
    )
    await cb.answer()


# Keep old states working too
@router.callback_query(ComplaintStates.select_reason, F.data.startswith("complaint_reason:"))
async def complaint_reason_old(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    await complaint_reason(cb, user, state)


@router.message(ComplaintExtStates.enter_detail)
@router.message(ComplaintStates.enter_detail)
async def complaint_detail(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    reason_key = data.get("complaint_reason", "other")
    detail = (message.text or "").strip()

    if len(detail) < 5:
        hint = (
            "Biroz batafsil yozing 😊 (kamida 5 ta belgi)"
            if lang == "uz" else
            "Напишите чуть подробнее 😊 (минимум 5 символов)"
        )
        await message.answer(hint)
        return

    against_id = data.get("against_id") or (user.id if user else 0)
    against_name = data.get("against_name", "Noma'lum")

    async with get_session() as session:
        from database.models import Complaint
        complaint = Complaint(
            from_id=user.id if user else 0,
            against_id=against_id,
            reason=f"[{reason_key}] {detail}",
            status=ComplaintStatus.new,
        )
        session.add(complaint)

    from config import config
    from bot.utils.notifications import notify_admins
    admin_text = (
        f"🚨 <b>Yangi shikoyat!</b>\n\n"
        f"Kim: @{message.from_user.username or (user.id if user else '?')}\n"
        f"Kimga: {against_name} (ID: {against_id})\n"
        f"Sabab: {reason_key}\n"
        f"Tafsil: {detail}"
    )
    await notify_admins(message.bot, config.bot.admin_ids, admin_text)

    await state.clear()
    await message.answer(
        t(lang, "COMPLAINT_SENT"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    logger.info("🚨 Shikoyat yuborildi: from={} against={}", user.id if user else "?", against_id)


# ─── S-53: YORDAM ────────────────────────────

@router.callback_query(F.data == "menu:help")
async def help_menu(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    await cb.message.edit_text(
        t(lang, "HELP_TEXT"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-54: SOZLAMALAR ────────────────────────

@router.callback_query(F.data == "menu:settings")
async def settings_menu(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    await cb.message.edit_text(
        t(lang, "SETTINGS_TITLE"),
        reply_markup=settings_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "settings:lang")
async def settings_change_lang(cb: CallbackQuery) -> None:
    await cb.message.edit_text(
        "Tilni tanlang / Выберите язык:",
        reply_markup=lang_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "settings:country")
async def settings_change_country(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    await cb.message.edit_text(
        t(lang, "SELECT_COUNTRY"),
        reply_markup=country_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "settings:phone")
async def settings_change_phone(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    from bot.states.states import SenderRegistration
    await state.set_state(SenderRegistration.phone)
    await cb.message.edit_text(
        t(lang, "ENTER_PHONE"),
        reply_markup=nav_keyboard(lang, "menu:settings"),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "settings:delete")
async def settings_delete_account(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    confirm_text = (
        "⚠️ Akkauntingizni o'chirishni tasdiqlaysizmi?\nBu amalni qaytarib bo'lmaydi!"
        if lang == "uz" else
        "⚠️ Вы уверены, что хотите удалить аккаунт?\nЭто действие нельзя отменить!"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="🗑 Ha, o'chiraman", callback_data="settings:delete_confirm")
        kb.button(text="❌ Bekor qilish", callback_data="menu:settings")
    else:
        kb.button(text="🗑 Да, удалить", callback_data="settings:delete_confirm")
        kb.button(text="❌ Отмена", callback_data="menu:settings")
    kb.adjust(2)
    await cb.message.edit_text(confirm_text, reply_markup=kb.as_markup())
    await cb.answer()


@router.callback_query(F.data == "settings:delete_confirm")
async def delete_account_confirm(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    if user:
        async with get_session() as session:
            await UserRepo.update(session, user.id, is_blocked=True, phone="deleted")
    bye = (
        "✅ Akkauntingiz o'chirildi. Xayr! 👋"
        if lang == "uz" else
        "✅ Аккаунт удалён. До свидания! 👋"
    )
    await cb.message.edit_text(bye)
    await cb.answer()
    logger.info("🗑 Akkaunt o'chirildi: user={}", user.id if user else "?")


@router.callback_query(F.data == "settings:notify")
async def settings_notify(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    msg = (
        "🔔 Bildirishnomalar hozircha doim yoqilgan.\n\n(Kelajakda bu yerdan sozlash mumkin bo'ladi)"
        if lang == "uz" else
        "🔔 Уведомления сейчас всегда включены.\n\n(В будущем здесь можно будет настроить)"
    )
    await cb.answer(msg, show_alert=True)


# ─── AEROPORT QOIDALARI ──────────────────────

AIRPORT_RULES = {
    "carry_on": {
        "uz": (
            "🎒 <b>Qo'l yukiga (ручная кладь) nima olish mumkin?</b>\n\n"
            "✅ <b>Ruxsat etiladi:</b>\n"
            "• Kiyim-kechak va shaxsiy buyumlar\n"
            "• Laptop, planshet, telefon\n"
            "• Suyuqliklar — <b>har biri 100ml gacha</b>, jami 1L shaffof sumkada\n"
            "• Dori-darmonlar (retsept bilan)\n"
            "• Bolalar oziq-ovqati\n"
            "• Kitob, jurnal\n"
            "• Kamera\n\n"
            "⚠️ <b>Eslatma:</b> Hajm odatda 55×40×20 sm, og'irligi 10 kg gacha.\n"
            "Aviakompaniyaga qarab farq qilishi mumkin!"
        ),
        "ru": (
            "🎒 <b>Что можно взять в ручную кладь?</b>\n\n"
            "✅ <b>Разрешено:</b>\n"
            "• Одежда и личные вещи\n"
            "• Ноутбук, планшет, телефон\n"
            "• Жидкости — <b>до 100мл каждая</b>, всего 1л в прозрачном пакете\n"
            "• Лекарства (с рецептом)\n"
            "• Детское питание\n"
            "• Книги, журналы\n"
            "• Фотокамера\n\n"
            "⚠️ <b>Примечание:</b> Обычно 55×40×20 см, до 10 кг.\n"
            "Может отличаться в зависимости от авиакомпании!"
        ),
    },
    "baggage": {
        "uz": (
            "🧳 <b>Bagajga (зарегистрированный багаж) nima olish mumkin?</b>\n\n"
            "✅ <b>Ruxsat etiladi:</b>\n"
            "• Kiyim-kechak va barcha shaxsiy buyumlar\n"
            "• Suyuqliklar (100ml dan ko'p bo'lsa)\n"
            "• Parfyum, kremlar, shampun\n"
            "• Sport jihozlari (aviakompaniyaga bog'liq)\n"
            "• Elektronika (zaryad qurilmalari)\n"
            "• Oziq-ovqat mahsulotlari (quruq holatda)\n\n"
            "❌ <b>Bagajga ham ruxsat etilmaydi:</b>\n"
            "• Li-ion batareyalar (>100Wh) — faqat qo'l yukida\n"
            "• Portlovchi moddalar\n"
            "• Oquvchi suyuqliklar (yaxshi o'ramasangiz)\n\n"
            "⚠️ Og'irlik: odatda 23 kg yoki 32 kg (ticket turiga qarab)"
        ),
        "ru": (
            "🧳 <b>Что можно сдать в багаж?</b>\n\n"
            "✅ <b>Разрешено:</b>\n"
            "• Одежда и личные вещи\n"
            "• Жидкости (более 100мл)\n"
            "• Духи, кремы, шампунь\n"
            "• Спортивный инвентарь (зависит от авиакомпании)\n"
            "• Электроника (зарядные устройства)\n"
            "• Продукты питания (в сухом виде)\n\n"
            "❌ <b>В багаж тоже нельзя:</b>\n"
            "• Li-ion аккумуляторы (>100Wh) — только в ручную кладь\n"
            "• Взрывчатые вещества\n"
            "• Текущие жидкости (без упаковки)\n\n"
            "⚠️ Вес: обычно 23 кг или 32 кг (зависит от тарифа)"
        ),
    },
    "forbidden": {
        "uz": (
            "🚫 <b>MUTLAQO OLIB BO'LMAYDIGAN NARSALAR</b>\n\n"
            "❌ <b>Hech qanday sharoitda ruxsat etilmaydi:</b>\n"
            "• 💣 Portlovchi moddalar va o'q-dorilar\n"
            "• 🔫 Qurol-yarog' (maxsus ruxsatsiz)\n"
            "• ☢️ Radioaktiv materiallar\n"
            "• 🧨 Pirotexnika (petarda, olovdon)\n"
            "• 🦠 Biologik xavfli moddalar\n"
            "• 💊 Noqonuniy dori-darmonlar (narkotik)\n"
            "• 🔪 Pichoq, qilich (qo'l yukida)\n"
            "• 🧴 100ml dan ortiq suyuqliklar (qo'l yukida)\n"
            "• 🔋 Shikastlangan/siqilgan batareyalar\n"
            "• 🌿 O'simlik va hayvonlar (maxsus ruxsatsiz)\n\n"
            "⚠️ <b>Eslatma:</b> Toshkentga olib borilishi taqiqlangan mahsulotlar "
            "uchun O'zbekiston bojxona qoidalarini ham tekshiring!"
        ),
        "ru": (
            "🚫 <b>АБСОЛЮТНО ЗАПРЕЩЁННЫЕ ПРЕДМЕТЫ</b>\n\n"
            "❌ <b>Запрещено ни при каких условиях:</b>\n"
            "• 💣 Взрывчатые вещества и боеприпасы\n"
            "• 🔫 Оружие (без специального разрешения)\n"
            "• ☢️ Радиоактивные материалы\n"
            "• 🧨 Пиротехника (петарды, факелы)\n"
            "• 🦠 Биологически опасные вещества\n"
            "• 💊 Незаконные наркотики\n"
            "• 🔪 Ножи, сабли (в ручной клади)\n"
            "• 🧴 Жидкости >100мл (в ручной клади)\n"
            "• 🔋 Повреждённые/вздутые аккумуляторы\n"
            "• 🌿 Растения и животные (без разрешения)\n\n"
            "⚠️ <b>Важно:</b> Также проверьте таможенные правила "
            "Узбекистана для ввозимых товаров!"
        ),
    },
    "tips": {
        "uz": (
            "💡 <b>Foydali maslahatlar</b>\n\n"
            "📦 <b>Paket qilishda:</b>\n"
            "• Suyuqliklarni yaxshilab berkiting (zip-lock qopda)\n"
            "• Mo'rt narsalarni ko'pik bilan o'rang\n"
            "• Har bir paketga nom va manzil yozing\n\n"
            "✈️ <b>Aeroportda:</b>\n"
            "• Ro'yxatdan vaqtida o'ting (2–3 soat oldin)\n"
            "• Og'irlikni oldindan o'lchang\n"
            "• Qimmat buyumlarni yongizdagi yukda saqlang\n\n"
            "🇺🇿 <b>Toshkentga olib borish:</b>\n"
            "• Elektronika 1 dan ortiq bo'lsa bojxona e'lon qilining\n"
            "• Pul $5000 dan ortiq bo'lsa deklaratsiya to'ldiring\n"
            "• Dori-darmonlar uchun retsept yoki tib guvohnomasi oling\n\n"
            "💬 Savollaringiz bo'lsa adminga yozing!"
        ),
        "ru": (
            "💡 <b>Полезные советы</b>\n\n"
            "📦 <b>При упаковке:</b>\n"
            "• Жидкости плотно закрывайте (в zip-lock пакете)\n"
            "• Хрупкие вещи оберните пеной\n"
            "• На каждую посылку напишите имя и адрес\n\n"
            "✈️ <b>В аэропорту:</b>\n"
            "• Регистрируйтесь заранее (за 2–3 часа)\n"
            "• Взвесьте багаж заранее\n"
            "• Ценности держите при себе в ручной клади\n\n"
            "🇺🇿 <b>Ввоз в Узбекистан:</b>\n"
            "• Если электроники больше 1 шт — декларируйте\n"
            "• Наличные >$5000 — заполните декларацию\n"
            "• На лекарства возьмите рецепт или справку\n\n"
            "💬 Если есть вопросы — напишите администратору!"
        ),
    },
}


@router.callback_query(F.data == "menu:airport_rules")
async def airport_rules_menu(cb: CallbackQuery, user: User | None) -> None:
    from bot.keyboards.inline import airport_rules_keyboard
    lang = user.language if user else "uz"
    text = (
        "🚫 <b>Aeroport qoidalari</b>\n\n"
        "Qo'l yuk va bagajga nima olish mumkin — barchasi shu yerda.\n\n"
        "Bo'limni tanlang 👇"
        if lang == "uz" else
        "🚫 <b>Правила аэропорта</b>\n\n"
        "Что можно брать в ручную кладь и багаж — всё здесь.\n\n"
        "Выберите раздел 👇"
    )
    await cb.message.edit_text(text, reply_markup=airport_rules_keyboard(lang), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("airport:"))
async def airport_rules_section(cb: CallbackQuery, user: User | None) -> None:
    from bot.keyboards.inline import airport_rules_keyboard
    lang = user.language if user else "uz"
    section = cb.data.split(":", 1)[1]

    rule_data = AIRPORT_RULES.get(section, {})
    text = rule_data.get(lang, rule_data.get("uz", "Ma'lumot topilmadi"))

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    back = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"
    kb.button(text=back, callback_data="menu:airport_rules")
    kb.button(text="🏠 Bosh menyu" if lang == "uz" else "🏠 Главное меню", callback_data="back:main")
    kb.adjust(2)

    await cb.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()
