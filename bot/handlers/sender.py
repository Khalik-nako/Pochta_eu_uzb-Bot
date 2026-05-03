"""
Sender flow handler — S-10 through S-17.
User can search for couriers and send requests.
"""
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from loguru import logger

from database import get_session, UserRepo, ListingRepo, DealRepo, SubscriptionRepo
from database.models import User, DealStatus
from locales import t
from bot.states.states import SenderRegistration, SenderSearch
from bot.keyboards.inline import (
    nav_keyboard, courier_sort_keyboard, courier_card_keyboard,
    no_couriers_keyboard, confirm_request_keyboard, back_to_menu_keyboard,
    month_keyboard,
)
from bot.utils.validators import (
    validate_fullname, validate_phone, get_available_months,
)
from bot.utils.notifications import notify_courier_new_request
from config import config, COUNTRY_PHONE_EXAMPLES

router = Router(name="sender")


# ─── HELPERS ─────────────────────────────────

def _phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    btn = "📱 Telefon raqamni ulashish" if lang == "uz" else "📱 Поделиться номером"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _location_keyboard(lang: str) -> ReplyKeyboardMarkup:
    btn = "📍 Lokatsiyamni yuborish" if lang == "uz" else "📍 Отправить местоположение"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ─── MAIN MENU: SENDER ───────────────────────

@router.callback_query(F.data == "menu:sender")
async def menu_sender(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"

    if user and user.phone and not user.phone.startswith("pending"):
        # Already registered — go straight to month picker
        await state.set_state(SenderRegistration.select_month)
        months = get_available_months(6)
        await cb.message.edit_text(
            t(lang, "SELECT_MONTH"),
            reply_markup=month_keyboard(lang, [(m[0], m[1]) for m in months]),
            parse_mode="HTML",
        )
    else:
        # First time — collect name
        await state.set_state(SenderRegistration.fullname)
        await cb.message.edit_text(
            t(lang, "ENTER_FULLNAME"),
            reply_markup=nav_keyboard(lang, "back:main"),
            parse_mode="HTML",
        )
    await cb.answer()


# ─── S-10: FULL NAME ──────────────────────────

@router.message(SenderRegistration.fullname)
async def enter_fullname(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    name = validate_fullname(message.text or "")

    if not name:
        err = (
            "❌ Ism familya to'g'ri emas 😊\n\n"
            "Ism va familyangizni to'liq kiriting.\n<i>Masalan: Alisher Karimov</i>\n\n"
            "⚠️ Faqat harflardan iborat bo'lishi kerak."
            if lang == "uz" else
            "❌ Имя введено неверно 😊\n\n"
            "Введите имя и фамилию полностью.\n<i>Например: Алишер Каримов</i>\n\n"
            "⚠️ Допускаются только буквы."
        )
        await message.answer(err, parse_mode="HTML")
        return

    await state.update_data(fullname=name)
    await state.set_state(SenderRegistration.phone)

    country = user.country if user else "Latviya"
    phone_example = COUNTRY_PHONE_EXAMPLES.get(country, "+371 2345 6789")
    text = (
        f"Telefon raqamingizni kiriting:\n\n<i>Masalan: {phone_example}</i>\n\n"
        "📱 Yoki quyidagi tugmani bosib ulashing:"
        if lang == "uz" else
        f"Введите номер телефона:\n\n<i>Например: {phone_example}</i>\n\n"
        "📱 Или поделитесь кнопкой ниже:"
    )
    await message.answer(text, reply_markup=_phone_keyboard(lang), parse_mode="HTML")


# ─── S-11: PHONE ────────────────────────────

@router.message(SenderRegistration.phone, F.contact)
async def enter_phone_contact(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    raw = message.contact.phone_number
    if not raw.startswith("+"):
        raw = "+" + raw
    phone = validate_phone(raw)
    if not phone:
        await message.answer(
            "❌ Raqam to'g'ri emas." if lang == "uz" else "❌ Неверный номер.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await _save_phone(message, user, state, lang, phone)


@router.message(SenderRegistration.phone)
async def enter_phone_text(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    country = user.country if user else "Latviya"
    phone_example = COUNTRY_PHONE_EXAMPLES.get(country, "+371 2345 6789")

    if not message.text:
        await message.answer(
            f"❌ Telefon raqamingizni kiriting.\n<i>Masalan: {phone_example}</i>"
            if lang == "uz" else
            f"❌ Введите номер телефона.\n<i>Например: {phone_example}</i>",
            reply_markup=_phone_keyboard(lang),
            parse_mode="HTML",
        )
        return

    phone = validate_phone(message.text)
    if not phone:
        err = (
            f"❌ Telefon raqam to'g'ri emas 😊\n\n"
            f"Davlat kodi bilan kiriting:\n<i>Masalan: {phone_example}</i>\n\n"
            "Yoki pastdagi tugmani bosing 👇"
            if lang == "uz" else
            f"❌ Номер телефона неверный 😊\n\n"
            f"Введите с кодом страны:\n<i>Например: {phone_example}</i>\n\n"
            "Или нажмите кнопку ниже 👇"
        )
        await message.answer(err, reply_markup=_phone_keyboard(lang), parse_mode="HTML")
        return

    await _save_phone(message, user, state, lang, phone)


async def _save_phone(message: Message, user: User | None, state: FSMContext, lang: str, phone: str) -> None:
    async with get_session() as session:
        existing = await UserRepo.get_by_phone(session, phone)
        if existing and existing.id != (user.id if user else 0):
            await message.answer(
                t(lang, "PHONE_ALREADY_EXISTS"),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML",
            )
            return

    await state.update_data(phone=phone)
    await state.set_state(SenderRegistration.location)
    await message.answer(
        "✅ Telefon saqlandi!\n\n📍 Joylashuvingizni yuboring\nBu kuryer sizga yaqinroq bo'lsin uchun kerak."
        if lang == "uz" else
        "✅ Телефон сохранён!\n\n📍 Отправьте своё местоположение\nЭто нужно для поиска ближайшего курьера.",
        reply_markup=_location_keyboard(lang),
    )


# ─── S-12: LOCATION ──────────────────────────
# CRITICAL: F.location handler MUST be registered BEFORE the generic fallback.
# In aiogram 3, handler priority is determined by registration order.

@router.message(SenderRegistration.location, F.location)
async def enter_location(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    loc = message.location
    data = await state.get_data()

    async with get_session() as session:
        uid = user.id if user else message.from_user.id
        await UserRepo.update(
            session, uid,
            full_name=data.get("fullname", user.full_name if user else "Unknown"),
            phone=data.get("phone", user.phone if user else None),
            lat=loc.latitude,
            lon=loc.longitude,
        )

    await message.answer("✅", reply_markup=ReplyKeyboardRemove())
    await state.update_data(lat=loc.latitude, lon=loc.longitude)
    await state.set_state(SenderRegistration.select_month)

    months = get_available_months(6)
    await message.answer(
        t(lang, "SELECT_MONTH"),
        reply_markup=month_keyboard(lang, [(m[0], m[1]) for m in months]),
        parse_mode="HTML",
    )


@router.message(SenderRegistration.location)
async def location_prompt(message: Message, user: User | None) -> None:
    """Catch anything that isn't a location and prompt the user."""
    lang = user.language if user else "uz"
    await message.answer(
        "📍 Iltimos, <b>lokatsiya</b> yuboring!\n\nPastdagi tugmani bosing 👇"
        if lang == "uz" else
        "📍 Пожалуйста, отправьте <b>геолокацию</b>!\n\nНажмите кнопку ниже 👇",
        reply_markup=_location_keyboard(lang),
        parse_mode="HTML",
    )


# ─── S-13: MONTH PICKER ──────────────────────

@router.callback_query(F.data.startswith("month:"))
async def select_month(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    month_str = cb.data.split(":", 1)[1]  # "2026-05"
    year, month = map(int, month_str.split("-"))
    await state.update_data(year=year, month=month)
    await _show_couriers(cb, user, state, sort_by="date")


# ─── S-14: COURIER LIST ──────────────────────

async def _show_couriers(
    cb: CallbackQuery,
    user: User | None,
    state: FSMContext,
    sort_by: str = "date",
) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    year = data.get("year")
    month = data.get("month")
    country = user.country if user else "Latviya"

    async with get_session() as session:
        listings = await ListingRepo.get_active_by_month(
            session, country=country, year=year, month=month, sort_by=sort_by
        )

    if not listings:
        await cb.message.edit_text(
            t(lang, "NO_COURIERS"),
            reply_markup=no_couriers_keyboard(lang),
            parse_mode="HTML",
        )
        await state.update_data(waiting_country=country, waiting_month=f"{year}-{month:02d}")
        await cb.answer()
        return

    await cb.message.edit_text(
        t(lang, "COURIERS_FOUND"),
        reply_markup=courier_sort_keyboard(lang),
        parse_mode="HTML",
    )

    from locales import get_messages
    msgs = get_messages(lang)
    for listing in listings[:10]:
        restrictions = ", ".join(listing.restrictions or [])
        if listing.custom_restriction:
            restrictions += f", {listing.custom_restriction}"
        name_parts = listing.user.full_name.split()
        short_name = name_parts[0] + " " + name_parts[-1][0] + "." if name_parts else "?"
        rating = listing.user.rating
        card_text = msgs.courier_card(
            name=short_name,
            city=listing.from_city,
            date=listing.flight_date.strftime("%d.%m.%Y"),
            time=listing.flight_time,
            max_kg=listing.max_kg,
            price=listing.price_per_kg,
            rating=round(rating, 1) if rating else "—",
            deal_count=listing.user.deal_count,
            restrictions=restrictions or "—",
        )
        await cb.message.answer(
            card_text,
            parse_mode="HTML",
            reply_markup=courier_card_keyboard(lang, listing.id),
        )

    await cb.answer()


@router.callback_query(F.data.startswith("sort:"))
async def sort_couriers(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    sort_by = cb.data.split(":", 1)[1]
    await _show_couriers(cb, user, state, sort_by=sort_by)


# ─── SUBSCRIPTION ────────────────────────────

@router.callback_query(F.data == "subscribe:yes")
async def subscribe_notify(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    country = data.get("waiting_country", user.country if user else "Latviya")
    month = data.get("waiting_month", "2026-05")

    if user:
        async with get_session() as session:
            await SubscriptionRepo.add(session, user.id, country, month)

    await cb.message.edit_text(t(lang, "SUBSCRIBED_NOTIFY"))
    await cb.answer()


@router.callback_query(F.data == "subscribe:no")
async def skip_subscribe(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    await cb.message.edit_text(
        t(lang, "MAIN_MENU"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-15: COURIER DETAIL ────────────────────

@router.callback_query(F.data.startswith("courier_detail:"))
async def courier_detail(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    listing_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)

    if not listing:
        await cb.answer("❌ Topilmadi")
        return

    restrictions = ", ".join(listing.restrictions or [])
    if listing.custom_restriction:
        restrictions += f", {listing.custom_restriction}"

    if lang == "uz":
        text = (
            f"<b>{listing.user.full_name}</b>\n"
            f"📍 {listing.from_city} → Toshkent\n"
            f"📅 {listing.flight_date.strftime('%d.%m.%Y')} soat {listing.flight_time}\n"
            f"⚖️ Max: {listing.max_kg} kg\n"
            f"💶 €{listing.price_per_kg}/kg\n"
            f"⭐ Reyting: {listing.user.rating:.1f} ({listing.user.deal_count} ta deal)\n"
            f"🚫 Olmaydi: {restrictions or 'koʼrsatilmagan'}"
        )
    else:
        text = (
            f"<b>{listing.user.full_name}</b>\n"
            f"📍 {listing.from_city} → Ташкент\n"
            f"📅 {listing.flight_date.strftime('%d.%m.%Y')} в {listing.flight_time}\n"
            f"⚖️ Макс: {listing.max_kg} кг\n"
            f"💶 €{listing.price_per_kg}/кг\n"
            f"⭐ Рейтинг: {listing.user.rating:.1f} ({listing.user.deal_count} сделок)\n"
            f"🚫 Не принимает: {restrictions or 'не указано'}"
        )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Shu kuryerni tanlash" if lang == "uz" else "✅ Выбрать этого курьера",
        callback_data=f"courier_select:{listing_id}",
    )
    kb.button(
        text="⬅️ Ro'yxatga qaytish" if lang == "uz" else "⬅️ Вернуться к списку",
        callback_data="back:courier_list",
    )
    kb.adjust(1)

    await cb.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.update_data(selected_listing_id=listing_id)
    await cb.answer()


# ─── S-16: CONFIRM REQUEST ───────────────────

@router.callback_query(F.data.startswith("courier_select:"))
async def select_courier(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    listing_id = int(cb.data.split(":")[1])
    await state.update_data(selected_listing_id=listing_id)

    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)

    if not listing:
        await cb.answer("❌ Topilmadi")
        return

    name_parts = listing.user.full_name.split()
    short_name = name_parts[0] + " " + name_parts[-1][0] + "." if name_parts else "?"

    info = (
        f"\n\n---\n\n"
        f"<b>{'Kuryer' if lang == 'uz' else 'Курьер'}:</b> {short_name}\n"
        f"<b>{'Sana' if lang == 'uz' else 'Дата'}:</b> "
        f"{listing.flight_date.strftime('%d.%m.%Y')} · {listing.flight_time}\n"
        f"<b>Max:</b> {listing.max_kg} kg · €{listing.price_per_kg}/kg\n\n"
        + ("So'rov yuborasizmi?" if lang == "uz" else "Отправить запрос?")
    )

    await cb.message.edit_text(
        t(lang, "SCAM_WARNING") + info,
        reply_markup=confirm_request_keyboard(lang),
        parse_mode="HTML",
    )
    await state.set_state(SenderSearch.confirm_request)
    await cb.answer()


@router.callback_query(SenderSearch.confirm_request, F.data == "request:confirm")
async def confirm_request(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    listing_id = data.get("selected_listing_id")

    if not user or not listing_id:
        await cb.answer("❌ Xato")
        return

    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)
        if not listing:
            await cb.answer("❌ E'lon topilmadi")
            return

        deal = await DealRepo.create(
            session,
            listing_id=listing_id,
            sender_id=user.id,
            courier_id=listing.user_id,
            status=DealStatus.requested,
        )
        # Snapshot before session closes to avoid MissingGreenlet errors
        courier_id = listing.user_id
        courier_lang = listing.user.language
        from_city = listing.from_city
        flight_date_str = listing.flight_date.strftime("%d.%m.%Y")
        courier_name = listing.user.full_name.split()[0]
        deal_id = deal.id

    await notify_courier_new_request(
        cb.bot,
        courier_id=courier_id,
        courier_lang=courier_lang,
        deal_id=deal_id,
        sender_name=user.full_name,
        location=f"({user.lat:.2f}, {user.lon:.2f})" if user.lat else "—",
    )

    await cb.message.edit_text(
        t(lang, "REQUEST_SENT", courier_name=courier_name, city=from_city, date=flight_date_str),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await state.clear()
    await cb.answer()
    logger.info("Deal created: id={} sender={} courier={}", deal_id, user.id, courier_id)


@router.callback_query(F.data == "request:cancel")
async def cancel_request(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.clear()
    await cb.message.edit_text(
        t(lang, "MAIN_MENU"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()
