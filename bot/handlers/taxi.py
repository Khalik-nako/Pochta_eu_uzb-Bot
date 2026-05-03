"""
Taxi xizmati handlerlari — Yevropa bo'ylab.
Faqat admin taxi qo'shadi/o'zgartiradi.
Userlar ko'radi va adminga yozadi.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from database import get_session, TaxiRepo
from database.models import User, TaxiService
from locales import t
from bot.keyboards.inline import (
    taxi_list_keyboard, taxi_detail_keyboard,
    taxi_driver_register_keyboard, back_to_menu_keyboard,
)
from config import config

router = Router(name="taxi")


class TaxiDriverStates(StatesGroup):
    """Taxi haydovchi ro'yxatdan o'tish holatlari."""
    enter_countries = State()
    enter_cargo_types = State()
    enter_capacity = State()
    enter_description = State()


class AdminTaxiStates(StatesGroup):
    """Admin taxi boshqarish holatlari."""
    add_driver_id = State()
    add_countries = State()
    add_cargo = State()
    add_capacity = State()
    add_description = State()
    edit_field = State()
    edit_value = State()


# ─── TAXI ASOSIY SAHIFASI ────────────────────

@router.callback_query(F.data == "menu:taxi")
async def taxi_main(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"

    async with get_session() as session:
        taxis = await TaxiRepo.get_all_active(session)

    if lang == "uz":
        header = (
            "🚕 <b>Taxi — Yevropa bo'ylab</b>\n\n"
            "Yevropa davlatlari bo'ylab ishonchli taxi va yuk tashish xizmatlaridan foydalaning.\n\n"
            "📌 Pinlangan xizmatlar tepada ko'rsatiladi.\n"
            "💎 Diamond belgisi tasdiqlangan xizmat hisoblanadi.\n\n"
            "Agar siz taxi haydovchisi bo'lsangiz, pastdagi tugmani bosib so'rov yuboring — "
            "admin ko'rib chiqadi va e'loningizni qo'shadi."
        )
    else:
        header = (
            "🚕 <b>Такси — по Европе</b>\n\n"
            "Надёжные услуги такси и грузоперевозок по странам Европы.\n\n"
            "📌 Закреплённые сервисы показываются вверху.\n"
            "💎 Diamond означает проверенный сервис.\n\n"
            "Если вы водитель такси, нажмите кнопку ниже и отправьте заявку — "
            "администратор рассмотрит и добавит ваше объявление."
        )

    if not taxis:
        no_taxi = (
            "\n\n⏳ Hozircha taxi xizmatlari mavjud emas.\nTez orada qo'shiladi!"
            if lang == "uz" else
            "\n\n⏳ Пока нет доступных такси-сервисов.\nСкоро появятся!"
        )
        header += no_taxi

    await cb.message.edit_text(
        header,
        reply_markup=taxi_list_keyboard(lang, taxis),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── TAXI TAFSILOTI ──────────────────────────

@router.callback_query(F.data.startswith("taxi:view:"))
async def taxi_view(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    taxi_id = int(cb.data.split(":")[2])

    async with get_session() as session:
        taxi = await TaxiRepo.get(session, taxi_id)

    if not taxi:
        await cb.answer("❌ Topilmadi", show_alert=True)
        return

    pin_badge = "📌 <b>Pinlangan xizmat</b>\n" if taxi.is_pinned else ""
    diamond_badge = "💎 <b>Tasdiqlangan xizmat</b>\n" if taxi.has_diamond else "" if hasattr(taxi, "has_diamond") else ""
    driver_name = taxi.driver.full_name if taxi.driver else "—"

    if lang == "uz":
        text = (
            f"{pin_badge}{diamond_badge}"
            f"🚕 <b>Taxi xizmati</b>\n\n"
            f"👤 Haydovchi: <b>{driver_name}</b>\n"
            f"🌍 Davlatlar: <b>{taxi.countries}</b>\n"
            f"📦 Qabul qilinadigan yuklar: <b>{taxi.cargo_types}</b>\n"
            f"👥 Yo'lovchi sig'imi: <b>{taxi.passenger_capacity} kishi</b>\n"
        )
        if taxi.description:
            text += f"\n📝 <i>{taxi.description}</i>\n"
        text += "\n📩 Bog'lanish uchun pastdagi tugmani bosing:"
    else:
        text = (
            f"{pin_badge}{diamond_badge}"
            f"🚕 <b>Такси-сервис</b>\n\n"
            f"👤 Водитель: <b>{driver_name}</b>\n"
            f"🌍 Страны: <b>{taxi.countries}</b>\n"
            f"📦 Принимаемые грузы: <b>{taxi.cargo_types}</b>\n"
            f"👥 Вместимость: <b>{taxi.passenger_capacity} чел.</b>\n"
        )
        if taxi.description:
            text += f"\n📝 <i>{taxi.description}</i>\n"
        text += "\n📩 Нажмите кнопку ниже для связи:"

    await cb.message.edit_text(text, reply_markup=taxi_detail_keyboard(lang, taxi_id), parse_mode="HTML")
    await cb.answer()


# ─── TAXI HAYDOVCHI SO'ROVI ─────────────────

@router.callback_query(F.data == "taxi:register_driver")
async def taxi_register_driver(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"

    if lang == "uz":
        text = (
            "✍️ <b>Taxi haydovchisi sifatida ro'yxatdan o'tish</b>\n\n"
            "Quyidagi savollarga javob bering:\n\n"
            "1️⃣ Qaysi davlatlarga borasiz?\n"
            "2️⃣ Qanday turdagi yuklarni olasiz?\n"
            "3️⃣ Necha kishi olasiz?\n\n"
            "So'rovingiz adminga yuboriladi va ko'rib chiqilgandan keyin "
            "e'loningiz faollashtiriladi.\n\n"
            "Davom etishni xohlaysizmi?"
        )
    else:
        text = (
            "✍️ <b>Регистрация как таксист/водитель</b>\n\n"
            "Ответьте на следующие вопросы:\n\n"
            "1️⃣ В какие страны вы ездите?\n"
            "2️⃣ Какой тип грузов вы принимаете?\n"
            "3️⃣ Сколько пассажиров/мест?\n\n"
            "Заявка отправится администратору, после проверки "
            "ваше объявление будет активировано.\n\n"
            "Хотите продолжить?"
        )

    await cb.message.edit_text(text, reply_markup=taxi_driver_register_keyboard(lang), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "taxi:send_request")
async def taxi_send_request(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.set_state(TaxiDriverStates.enter_countries)

    prompt = (
        "🌍 <b>Qaysi davlatlarga borasiz?</b>\n\n"
        "Vergul bilan yozing:\n"
        "<i>Misol: Latviya, Litva, Estoniya, Germaniya</i>"
        if lang == "uz" else
        "🌍 <b>В какие страны вы ездите?</b>\n\n"
        "Перечислите через запятую:\n"
        "<i>Пример: Латвия, Литва, Эстония, Германия</i>"
    )
    await cb.message.edit_text(prompt, parse_mode="HTML")
    await cb.answer()


@router.message(TaxiDriverStates.enter_countries)
async def taxi_enter_countries(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.update_data(countries=message.text)

    prompt = (
        "📦 <b>Qanday turdagi yuklarni qabul qilasiz?</b>\n\n"
        "<i>Misol: Kichik posilkalar, Katta yuk, Shaxsiy narsalar, Faqat yo'lovchilar</i>"
        if lang == "uz" else
        "📦 <b>Какие грузы вы принимаете?</b>\n\n"
        "<i>Пример: Маленькие посылки, Крупный груз, Личные вещи, Только пассажиры</i>"
    )
    await state.set_state(TaxiDriverStates.enter_cargo_types)
    await message.answer(prompt, parse_mode="HTML")


@router.message(TaxiDriverStates.enter_cargo_types)
async def taxi_enter_cargo(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    await state.update_data(cargo_types=message.text)

    prompt = (
        "👥 <b>Necha kishi/o'rin bor?</b>\n\nFaqat raqam kiriting (masalan: 4)"
        if lang == "uz" else
        "👥 <b>Сколько мест/пассажиров?</b>\n\nВведите только цифру (например: 4)"
    )
    await state.set_state(TaxiDriverStates.enter_capacity)
    await message.answer(prompt, parse_mode="HTML")


@router.message(TaxiDriverStates.enter_capacity)
async def taxi_enter_capacity(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    if not message.text or not message.text.strip().isdigit():
        err = "❌ Faqat raqam kiriting!" if lang == "uz" else "❌ Введите только цифру!"
        await message.answer(err)
        return

    await state.update_data(capacity=int(message.text.strip()))
    prompt = (
        "📝 <b>Qo'shimcha ma'lumot (ixtiyoriy)</b>\n\n"
        "Narx, ish vaqti, bog'lanish usuli haqida yozing.\n"
        "O'tkazib yuborish uchun — va davom eting yoki matn yozing."
        if lang == "uz" else
        "📝 <b>Дополнительная информация (необязательно)</b>\n\n"
        "Напишите о цене, рабочих часах, способе связи.\n"
        "Чтобы пропустить — напишите «-» или любой текст."
    )
    await state.set_state(TaxiDriverStates.enter_description)
    await message.answer(prompt, parse_mode="HTML")


@router.message(TaxiDriverStates.enter_description)
async def taxi_enter_description(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    description = message.text if message.text and message.text != "-" else None

    # Adminga yuborish
    for admin_id in config.bot.admin_ids:
        try:
            admin_text = (
                f"🚕 <b>Yangi taxi so'rovi</b>\n\n"
                f"👤 Foydalanuvchi: {user.full_name} (ID: {user.id})\n"
                f"📞 Telefon: {user.phone}\n"
                f"🌍 Davlatlar: {data.get('countries', '—')}\n"
                f"📦 Yuklar: {data.get('cargo_types', '—')}\n"
                f"👥 Sig'im: {data.get('capacity', 4)} kishi\n"
                f"📝 Qo'shimcha: {description or '—'}\n\n"
                f"Tasdiqlash uchun: /admin → Taxi boshqarish"
            )
            kb = InlineKeyboardBuilder()
            kb.button(text="✅ Tasdiqlash va qo'shish", callback_data=f"admin_taxi:approve_req:{user.id}")
            kb.button(text="❌ Rad etish", callback_data=f"admin_taxi:reject_req:{user.id}")
            kb.adjust(1)
            await message.bot.send_message(admin_id, admin_text, parse_mode="HTML", reply_markup=kb.as_markup())
        except Exception as e:
            logger.error("❌ Admin {}ga taxi so'rovi yuborishda xato: {}", admin_id, e)

    await state.clear()
    confirm = (
        "✅ <b>So'rovingiz adminga yuborildi!</b>\n\n"
        "Ko'rib chiqilgandan keyin e'loningiz qo'shiladi va xabar olasiz. 🚕"
        if lang == "uz" else
        "✅ <b>Заявка отправлена администратору!</b>\n\n"
        "После проверки ваше объявление будет добавлено и вы получите уведомление. 🚕"
    )
    await message.answer(confirm, reply_markup=back_to_menu_keyboard(lang), parse_mode="HTML")
    logger.info("🚕 Taxi so'rovi yuborildi: user_id={}", user.id)


# ─── TAXI HAYDOVCHI BILAN BOG'LANISH ────────

@router.callback_query(F.data.startswith("taxi:contact:"))
async def taxi_contact(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    taxi_id = int(cb.data.split(":")[2])

    # Adminga xabar yuborish
    async with get_session() as session:
        taxi = await TaxiRepo.get(session, taxi_id)

    if not taxi:
        await cb.answer("❌ Topilmadi", show_alert=True)
        return

    user_info = (
        f"📩 <b>Taxi so'rov</b>\n\n"
        f"Foydalanuvchi: {user.full_name} (ID: {user.id})\n"
        f"Taxi: #{taxi_id} — {taxi.countries}\n\n"
        f"Foydalanuvchi bu taxi xizmati bilan bog'lanishni so'rayapti."
    )
    for admin_id in config.bot.admin_ids:
        try:
            await cb.bot.send_message(admin_id, user_info, parse_mode="HTML")
        except Exception:
            pass

    thanks = (
        "📩 <b>So'rovingiz yuborildi!</b>\n\n"
        "Admin tez orada taxi haydovchisi kontaktini yubboradi."
        if lang == "uz" else
        "📩 <b>Запрос отправлен!</b>\n\n"
        "Администратор скоро пришлёт контакт водителя."
    )
    await cb.answer(thanks, show_alert=True)
    logger.info("📩 Taxi kontakt so'rovi: user_id={} taxi_id={}", user.id, taxi_id)
