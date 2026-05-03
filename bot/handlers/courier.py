"""
Kuryer yo'li handler — S-20..S-28
Barcha muammolar tuzatildi:
- Video bo'lmagan xabar uchun xabar
- Lokatsiya uchun ReplyKeyboard tugmasi
- Telefon uchun ReplyKeyboard tugmasi
- Davlatga mos shaharlar
- Davlatga mos telefon misoli
- Orqaga tugmalar to'g'ri ishlaydi
"""
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from loguru import logger

from database import get_session, UserRepo, ListingRepo, BlacklistRepo
from database.models import User, ListingStatus
from locales import t
from bot.states.states import CourierRegistration
from bot.keyboards.inline import (
    nav_keyboard, restrictions_keyboard, back_to_menu_keyboard,
    admin_verify_keyboard, courier_departure_city_keyboard,
)
from bot.utils.validators import (
    validate_fullname, validate_phone, validate_date,
    validate_time, validate_kg, validate_price,
)
from bot.utils.notifications import notify_admins
from config import config, DEPARTURE_CITIES, COUNTRY_PHONE_EXAMPLES

router = Router(name="courier")


def _phone_example(country: str) -> str:
    return COUNTRY_PHONE_EXAMPLES.get(country, "+371 2345 6789")


def _location_keyboard(lang: str) -> ReplyKeyboardMarkup:
    btn_text = "📍 Lokatsiyamni yuborish" if lang == "uz" else "📍 Отправить местоположение"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    btn_text = "📱 Telefon raqamni ulashish" if lang == "uz" else "📱 Поделиться номером"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ─── MENYU ───────────────────────────────────

@router.callback_query(F.data == "menu:courier")
async def menu_courier(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.fullname)
    await cb.message.edit_text(
        t(lang, "ENTER_FULLNAME"),
        reply_markup=nav_keyboard(lang, "back:main"),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-20: ISM ───────────────────────────────

@router.message(CourierRegistration.fullname)
async def courier_fullname(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    name = validate_fullname(message.text or "")
    if not name:
        err = (
            "❌ Ism familya to'g'ri emas 😊\n\n"
            "Iltimos, ism va familyangizni to'liq kiriting.\n"
            "<i>Masalan: Alisher Karimov</i>\n\n"
            "⚠️ Faqat harflardan iborat bo'lishi kerak."
            if lang == "uz" else
            "❌ Имя введено неверно 😊\n\n"
            "Пожалуйста, введите имя и фамилию полностью.\n"
            "<i>Например: Алишер Каримов</i>\n\n"
            "⚠️ Допускаются только буквы."
        )
        await message.answer(err, parse_mode="HTML")
        return
    await state.update_data(fullname=name)
    await state.set_state(CourierRegistration.phone)

    country = user.country if user else "Latviya"
    phone_example = _phone_example(country)
    phone_text = (
        f"Telefon raqamingizni kiriting:\n\n"
        f"<i>Masalan: {phone_example}</i>\n\n"
        "📱 Yoki quyidagi tugmani bosib ulashing:"
        if lang == "uz" else
        f"Введите номер телефона:\n\n"
        f"<i>Например: {phone_example}</i>\n\n"
        "📱 Или поделитесь кнопкой ниже:"
    )
    await message.answer(phone_text, reply_markup=_phone_keyboard(lang), parse_mode="HTML")


# ─── S-21: TELEFON ───────────────────────────

@router.message(CourierRegistration.phone, F.contact)
async def courier_phone_contact(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    phone_raw = message.contact.phone_number
    if not phone_raw.startswith("+"):
        phone_raw = "+" + phone_raw
    phone = validate_phone(phone_raw)
    if not phone:
        await message.answer(
            "❌ Telefon raqam to'g'ri emas." if lang == "uz" else "❌ Неверный номер.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await _process_phone(message, user, state, lang, phone)


@router.message(CourierRegistration.phone)
async def courier_phone(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    country = user.country if user else "Latviya"
    phone_example = _phone_example(country)

    if not message.text:
        await message.answer(
            f"❌ Iltimos, telefon raqamingizni kiriting.\n<i>Masalan: {phone_example}</i>"
            if lang == "uz" else
            f"❌ Введите номер телефона.\n<i>Например: {phone_example}</i>",
            reply_markup=_phone_keyboard(lang), parse_mode="HTML",
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
    await _process_phone(message, user, state, lang, phone)


async def _process_phone(message, user, state, lang, phone):
    async with get_session() as session:
        if await BlacklistRepo.is_blocked(session, phone, message.from_user.id):
            await message.answer(
                "⛔ Sizning akkauntingiz bloklangan. Admin bilan bog'laning."
                if lang == "uz" else
                "⛔ Ваш аккаунт заблокирован. Свяжитесь с администратором.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        existing = await UserRepo.get_by_phone(session, phone)
        if existing and existing.id != (user.id if user else 0):
            await message.answer(
                t(lang, "PHONE_ALREADY_EXISTS"),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML",
            )
            return

    await state.update_data(phone=phone)
    await state.set_state(CourierRegistration.location)
    await message.answer(
        "✅ Telefon saqlandi!\n\n📍 Joylashuvingizni yuboring\nBu kuryer sizga yaqinroq bo'lsin uchun kerak."
        if lang == "uz" else
        "✅ Телефон сохранён!\n\n📍 Отправьте своё местоположение\nЭто нужно для поиска ближайшего курьера.",
        reply_markup=_location_keyboard(lang),
    )


# ─── S-22: LOKATSIYA ─────────────────────────

@router.message(CourierRegistration.location, F.location)
async def courier_location(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    loc = message.location
    await state.update_data(lat=loc.latitude, lon=loc.longitude)

    country = user.country if user else "Latviya"
    cities = DEPARTURE_CITIES.get(country, ["Riga"])

    await message.answer("✅", reply_markup=ReplyKeyboardRemove())

    city_prompt = (
        f"Qaysi shahardan uchmoqchisiz? ✈️\n<i>{country} uchun aeroportlar:</i>"
        if lang == "uz" else
        f"Из какого города вы летите? ✈️\n<i>Аэропорты для {country}:</i>"
    )
    await message.answer(
        city_prompt,
        reply_markup=courier_departure_city_keyboard(lang, cities),
        parse_mode="HTML",
    )


@router.message(CourierRegistration.location)
async def courier_location_wrong(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await message.answer(
        "📍 Iltimos, <b>lokatsiya</b> yuboring!\n\nPastdagi tugmani bosing 👇"
        if lang == "uz" else
        "📍 Пожалуйста, отправьте <b>геолокацию</b>!\n\nНажмите кнопку ниже 👇",
        reply_markup=_location_keyboard(lang),
        parse_mode="HTML",
    )


# ─── SHAHAR TANLASH ───────────────────────────

@router.callback_query(F.data.startswith("depcity:"))
async def select_departure_city(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    city = cb.data.split(":", 1)[1]
    if city != "other":
        await state.update_data(from_city=city)
    await state.set_state(CourierRegistration.flight_date)
    await cb.message.edit_text(
        t(lang, "ENTER_FLIGHT_DATE"),
        reply_markup=nav_keyboard(lang, "back:courier_location"),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── ORQAGA TUGMALARI ─────────────────────────

@router.callback_query(F.data == "back:courier_name")
async def back_courier_name(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.fullname)
    await cb.message.edit_text(t(lang, "ENTER_FULLNAME"), reply_markup=nav_keyboard(lang, "back:main"), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "back:courier_phone")
async def back_courier_phone(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    country = user.country if user else "Latviya"
    phone_example = _phone_example(country)
    await state.set_state(CourierRegistration.phone)
    await cb.message.edit_text(
        f"Telefon raqamingizni kiriting:\n\n<i>Masalan: {phone_example}</i>"
        if lang == "uz" else
        f"Введите номер телефона:\n\n<i>Например: {phone_example}</i>",
        reply_markup=nav_keyboard(lang, "back:courier_name"),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "back:courier_location")
async def back_courier_location(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.location)
    await cb.message.edit_text(
        "📍 Lokatsiyangizni yuboring" if lang == "uz" else "📍 Отправьте своё местоположение",
        reply_markup=nav_keyboard(lang, "back:courier_phone"),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data == "back:courier_date")
async def back_courier_date(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.flight_date)
    await cb.message.edit_text(t(lang, "ENTER_FLIGHT_DATE"), reply_markup=nav_keyboard(lang, "back:courier_location"), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "back:courier_time")
async def back_courier_time(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.flight_time)
    await cb.message.edit_text(t(lang, "ENTER_FLIGHT_TIME"), reply_markup=nav_keyboard(lang, "back:courier_date"), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "back:courier_kg")
async def back_courier_kg(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(CourierRegistration.max_kg)
    await cb.message.edit_text(t(lang, "ENTER_MAX_KG"), reply_markup=nav_keyboard(lang, "back:courier_time"), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "back:courier_restrictions")
async def back_courier_restrictions(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    selected = data.get("selected_restrictions", [])
    await state.set_state(CourierRegistration.restrictions)
    await cb.message.edit_text(t(lang, "SELECT_RESTRICTIONS"), reply_markup=restrictions_keyboard(lang, selected), parse_mode="HTML")
    await cb.answer()


# ─── S-23: SANA ──────────────────────────────

@router.message(CourierRegistration.flight_date)
async def courier_flight_date(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    d = validate_date(message.text or "")
    if not d:
        await message.answer(t(lang, "DATE_FORMAT_ERROR"))
        return
    await state.update_data(flight_date=d.isoformat())
    await state.set_state(CourierRegistration.flight_time)
    await message.answer(t(lang, "ENTER_FLIGHT_TIME"), reply_markup=nav_keyboard(lang, "back:courier_date"), parse_mode="HTML")


# ─── S-23: VAQT ──────────────────────────────

@router.message(CourierRegistration.flight_time)
async def courier_flight_time(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    time_str = validate_time(message.text or "")
    if not time_str:
        await message.answer(t(lang, "TIME_FORMAT_ERROR"))
        return
    await state.update_data(flight_time=time_str)
    await state.set_state(CourierRegistration.max_kg)
    await message.answer(t(lang, "ENTER_MAX_KG"), reply_markup=nav_keyboard(lang, "back:courier_time"), parse_mode="HTML")


# ─── S-24: KG ────────────────────────────────

@router.message(CourierRegistration.max_kg)
async def courier_max_kg(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    kg = validate_kg(message.text or "")
    if not kg:
        await message.answer(
            "❌ Kg noto'g'ri 😊 1–100 orasida raqam kiriting.\n<i>Masalan: 8</i>"
            if lang == "uz" else
            "❌ Неверное кг 😊 Введите число от 1 до 100.\n<i>Например: 8</i>",
            parse_mode="HTML",
        )
        return
    await state.update_data(max_kg=kg)
    await state.set_state(CourierRegistration.price_per_kg)
    await message.answer(t(lang, "ENTER_PRICE"), reply_markup=nav_keyboard(lang, "back:courier_kg"), parse_mode="HTML")


# ─── S-24: NARX ──────────────────────────────

@router.message(CourierRegistration.price_per_kg)
async def courier_price(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    price = validate_price(message.text or "")
    if not price:
        await message.answer(
            "❌ Narx noto'g'ri 😊 0.1–100 €/kg kiriting.\n<i>Masalan: 8</i>"
            if lang == "uz" else
            "❌ Неверная цена 😊 Введите от 0.1 до 100 €/кг.\n<i>Например: 8</i>",
            parse_mode="HTML",
        )
        return
    await state.update_data(price_per_kg=price, selected_restrictions=[])
    await state.set_state(CourierRegistration.restrictions)
    await message.answer(t(lang, "SELECT_RESTRICTIONS"), reply_markup=restrictions_keyboard(lang, []), parse_mode="HTML")


# ─── S-25: CHEKLOVLAR ────────────────────────

@router.callback_query(CourierRegistration.restrictions, F.data.startswith("restrict:"))
async def toggle_restriction(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    key = cb.data.split(":", 1)[1]
    data = await state.get_data()
    selected = data.get("selected_restrictions", [])

    if key == "done":
        await state.set_state(CourierRegistration.video)
        await cb.message.edit_text(
            t(lang, "SEND_VERIFICATION_VIDEO"),
            reply_markup=nav_keyboard(lang, "back:courier_restrictions"),
            parse_mode="HTML",
        )
        await cb.answer()
        return

    if key == "custom":
        await state.set_state(CourierRegistration.custom_restriction)
        await cb.message.edit_text(
            "✏️ Qo'shimcha cheklovni yozing:\n\n<i>Masalan: Parfyum, alkogol</i>"
            if lang == "uz" else
            "✏️ Введите дополнительное ограничение:\n\n<i>Например: Духи, алкоголь</i>",
            reply_markup=nav_keyboard(lang, "back:courier_restrictions"),
            parse_mode="HTML",
        )
        await cb.answer()
        return

    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)

    await state.update_data(selected_restrictions=selected)
    await cb.message.edit_reply_markup(reply_markup=restrictions_keyboard(lang, selected))
    await cb.answer()


@router.message(CourierRegistration.custom_restriction)
async def courier_custom_restriction(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    text = (message.text or "").strip()
    if text:
        await state.update_data(custom_restriction=text)
    await state.set_state(CourierRegistration.video)
    await message.answer(t(lang, "SEND_VERIFICATION_VIDEO"), reply_markup=nav_keyboard(lang, "back:courier_restrictions"), parse_mode="HTML")


# ─── S-26: VIDEO VERIFIKATSIYA ───────────────

@router.message(CourierRegistration.video, F.video | F.video_note)
async def courier_video(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()

    msg_id = message.message_id
    is_video_note = message.video_note is not None
    video_file_id = message.video.file_id if message.video else message.video_note.file_id

    # Kanalga yuboriladigan ma'lumot matni
    name = data.get("fullname", user.full_name if user else "Noma'lum")
    country = user.country if user else "—"
    from_city = data.get("from_city", "Riga")
    all_restrictions = data.get("selected_restrictions", []) + (
        [data["custom_restriction"]] if data.get("custom_restriction") else []
    )
    channel_info = (
        "👤 " + name + "\n"
        "📱 " + data.get("phone", "—") + "\n"
        "🌍 " + country + " · " + from_city + " → Toshkent\n"
        "📅 " + data["flight_date"] + " · " + data["flight_time"] + "\n"
        "⚖️ " + str(data["max_kg"]) + " kg · €" + str(data["price_per_kg"]) + "/kg\n"
        "🚫 " + (", ".join(all_restrictions) or "—")
    )

    video_msg_id = str(video_file_id)[:50]  # fallback
    channel_caption = "\u2139\ufe0f <b>Kuryer ma\'lumotlari:</b>\n\n" + channel_info

    try:
        if is_video_note:
            # Doiracha video — caption qo'shib bo'lmaydi
            # Avval videoni forward qilamiz, keyin alohida xabar
            forwarded = await message.bot.forward_message(
                chat_id=config.channel.video_channel_id,
                from_chat_id=message.chat.id,
                message_id=msg_id,
            )
            video_msg_id = str(forwarded.message_id)
            # Alohida ma'lumot xabari (reply sifatida)
            await message.bot.send_message(
                chat_id=config.channel.video_channel_id,
                text=channel_caption,
                reply_to_message_id=forwarded.message_id,
                parse_mode="HTML",
            )
        else:
            # Oddiy video — caption bilan copy_message
            sent = await message.bot.copy_message(
                chat_id=config.channel.video_channel_id,
                from_chat_id=message.chat.id,
                message_id=msg_id,
                caption=channel_caption,
                parse_mode="HTML",
            )
            video_msg_id = str(sent.message_id)
    except Exception as e:
        logger.error("\u274c Videoni kanalga yuborishda xato: {}", e)

    from datetime import date as dclass
    async with get_session() as session:
        if user:
            await UserRepo.update(
                session, user.id,
                full_name=data.get("fullname", user.full_name),
                phone=data.get("phone", user.phone),
                lat=data.get("lat", user.lat),
                lon=data.get("lon", user.lon),
            )

        flight_date = dclass.fromisoformat(data["flight_date"])
        listing = await ListingRepo.create(
            session,
            user_id=message.from_user.id,
            from_country=user.country if user else "Latviya",
            from_city=data.get("from_city", "Riga"),
            flight_date=flight_date,
            flight_time=data["flight_time"],
            max_kg=data["max_kg"],
            price_per_kg=data["price_per_kg"],
            restrictions=data.get("selected_restrictions", []),
            custom_restriction=data.get("custom_restriction"),
            video_msg_id=video_msg_id,
            status=ListingStatus.pending,
        )

    admin_text = (
        f"🆕 <b>Yangi kuryer so'rovi!</b>\n\n"
        f"👤 Ism: {name}\n"
        f"📱 Telefon: {data.get('phone', '—')}\n"
        f"🌍 Davlat: {country}\n"
        f"📍 Yo'nalish: {from_city} → Toshkent\n"
        f"📅 Sana: {data['flight_date']} · {data['flight_time']}\n"
        f"⚖️ Max yuk: {data['max_kg']} kg · 💶 €{data['price_per_kg']}/kg\n"
        f"🚫 Olmaydi: {', '.join(all_restrictions) or '—'}\n\n"
        f"🆔 Listing ID: {listing.id}\n\n"
        f"⚠️ <b>TASDIQLASH KERAK!</b> Pastdagi tugmalarni bosing:"
    )
    await notify_admins(message.bot, config.bot.admin_ids, admin_text)

    for admin_id in config.bot.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"🎥 Video msg_id: {video_msg_id}\n▶️ Videoni ko'rish va tasdiqlash uchun:",
                reply_markup=admin_verify_keyboard(listing.id),
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(t(lang, "VIDEO_SENT_WAITING"), reply_markup=back_to_menu_keyboard(lang), parse_mode="HTML")
    logger.info("🎥 Kuryer videosi yuborildi: listing_id={} user_id={}", listing.id, message.from_user.id)


@router.message(CourierRegistration.video)
async def courier_video_wrong(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await message.answer(
        "🎥 Iltimos, faqat <b>video</b> yoki <b>video xabar (doiracha)</b> yuboring!\n\n"
        "📹 Qanday yuborish:\n"
        "• Kamera orqali video oling\n"
        "• Galereyadagi videoni yuboring\n"
        "• 🎤 tugmani ushlab turing → video xabar\n\n"
        "❌ Rasm, matn, hujjat qabul qilinmaydi."
        if lang == "uz" else
        "🎥 Пожалуйста, отправьте <b>видео</b> или <b>видео-кружок</b>!\n\n"
        "📹 Как отправить:\n"
        "• Снимите видео через камеру\n"
        "• Отправьте видео из галереи\n"
        "• Зажмите 🎤 → видеокружок\n\n"
        "❌ Фото, текст, документ не принимаются.",
        reply_markup=nav_keyboard(lang, "back:courier_restrictions"),
        parse_mode="HTML",
    )
