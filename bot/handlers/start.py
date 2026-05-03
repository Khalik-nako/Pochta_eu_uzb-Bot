"""
Start / onboarding handlers — language, country, legal, main menu.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from database import get_session, UserRepo
from database.models import User
from locales import t
from bot.keyboards.inline import (
    lang_keyboard, country_keyboard, legal_keyboard,
    main_menu_keyboard, back_to_menu_keyboard, nav_keyboard,
)
from config import COUNTRY_TIMEZONES, COUNTRY_PHONE_EXAMPLES

router = Router(name="start")


# ─── /start ──────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, user: User | None, state: FSMContext) -> None:
    await state.clear()

    if user:
        first_name = user.full_name.split()[0] if user.full_name else ""
        lang = user.language
        welcome_back = (
            f"Qaytib keldingiz, <b>{first_name}</b>! 👋\n\nNima qilmoqchisiz?"
            if lang == "uz" else
            f"С возвращением, <b>{first_name}</b>! 👋\n\nЧто хотите сделать?"
        )
        await message.answer(welcome_back, reply_markup=main_menu_keyboard(lang))
        logger.info("Returning user: {}", user.id)
    else:
        await message.answer(t("uz", "START_WELCOME"), reply_markup=lang_keyboard())


# ─── LANGUAGE SELECTION ──────────────────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def select_language(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = cb.data.split(":")[1]
    await state.update_data(lang=lang)

    if user:
        async with get_session() as session:
            await UserRepo.update(session, user.id, language=lang)
        await cb.message.edit_text(t(lang, "MAIN_MENU"), reply_markup=main_menu_keyboard(lang))
    else:
        await cb.message.edit_text(t(lang, "SELECT_COUNTRY"), reply_markup=country_keyboard(lang))
    await cb.answer()


# ─── COUNTRY SELECTION ───────────────────────────────────────

@router.callback_query(F.data.startswith("country:"))
async def select_country(cb: CallbackQuery, state: FSMContext) -> None:
    country = cb.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "uz")

    await state.update_data(
        country=country,
        timezone=COUNTRY_TIMEZONES.get(country, "Europe/Riga"),
    )
    await cb.message.edit_text(t(lang, "LEGAL_TEXT"), reply_markup=legal_keyboard(lang))
    await cb.answer()


# ─── LEGAL ACCEPT ────────────────────────────────────────────

@router.callback_query(F.data == "legal:accept")
async def accept_legal(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "uz")
    country = data.get("country", "Latviya")
    timezone = data.get("timezone", "Europe/Riga")

    async with get_session() as session:
        existing = await UserRepo.get(session, cb.from_user.id)
        if not existing:
            await UserRepo.create(
                session,
                id=cb.from_user.id,
                full_name=cb.from_user.full_name or "Unknown",
                phone=f"pending:{cb.from_user.id}",
                language=lang,
                country=country,
                timezone=timezone,
                legal_accepted=True,
            )

    await state.clear()
    await cb.message.edit_text(t(lang, "MAIN_MENU"), reply_markup=main_menu_keyboard(lang))
    await cb.answer(t(lang, "LEGAL_ACCEPTED"))
    logger.info("New user accepted legal: {}", cb.from_user.id)


# ─── BACK: MAIN MENU ─────────────────────────────────────────

@router.callback_query(F.data == "back:main")
async def back_to_main_menu(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    await state.clear()
    lang = user.language if user else "uz"
    await cb.message.edit_text(t(lang, "MAIN_MENU"), reply_markup=main_menu_keyboard(lang))
    await cb.answer()


# ─── BACK: LANGUAGE (from country selection) ─────────────────

@router.callback_query(F.data == "back:start")
async def back_to_start(cb: CallbackQuery, state: FSMContext) -> None:
    await cb.message.edit_text(t("uz", "START_WELCOME"), reply_markup=lang_keyboard())
    await cb.answer()


# ─── BACK: SENDER MONTH (go back to month picker) ────────────

@router.callback_query(F.data == "back:sender_month")
async def back_to_sender_month(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    from bot.states.states import SenderRegistration
    from bot.utils.validators import get_available_months
    from bot.keyboards.inline import month_keyboard

    lang = user.language if user else "uz"
    await state.set_state(SenderRegistration.select_month)
    months = get_available_months(6)
    await cb.message.edit_text(
        t(lang, "SELECT_MONTH"),
        reply_markup=month_keyboard(lang, [(m[0], m[1]) for m in months]),
    )
    await cb.answer()


# ─── GENERIC BACK HANDLER (catch-all for unhandled back:*) ───

@router.callback_query(F.data.startswith("back:"))
async def generic_back(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    """Fallback for any back:* callback that isn't handled specifically."""
    lang = user.language if user else "uz"
    await state.clear()
    await cb.message.edit_text(t(lang, "MAIN_MENU"), reply_markup=main_menu_keyboard(lang))
    await cb.answer()


# ─── COMMANDS ────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, user: User | None, state: FSMContext) -> None:
    await state.clear()
    lang = user.language if user else "uz"
    await message.answer(t(lang, "MAIN_MENU"), reply_markup=main_menu_keyboard(lang))


@router.message(Command("help"))
async def cmd_help(message: Message, user: User | None) -> None:
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    lang = user.language if user else "uz"
    kb = InlineKeyboardBuilder()
    if lang == "uz":
        kb.button(text="📖 Qoidalar", callback_data="menu:airport_rules")
        kb.button(text="🚨 Shikoyat", callback_data="menu:complaint")
        kb.button(text="🏠 Bosh menyu", callback_data="back:main")
    else:
        kb.button(text="📖 Правила", callback_data="menu:airport_rules")
        kb.button(text="🚨 Жалоба", callback_data="menu:complaint")
        kb.button(text="🏠 Главное меню", callback_data="back:main")
    kb.adjust(2, 1)
    await message.answer(t(lang, "HELP_TEXT"), reply_markup=kb.as_markup())


@router.message(Command("my_orders"))
async def cmd_my_orders(message: Message, user: User | None, state: FSMContext) -> None:
    await state.clear()
    lang = user.language if user else "uz"
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start" if lang == "uz" else "❌ Сначала зарегистрируйтесь: /start")
        return
    from bot.keyboards.inline import listings_filter_keyboard
    await message.answer(t(lang, "MY_LISTINGS_TITLE"), reply_markup=listings_filter_keyboard(lang))


@router.message(Command("rating"))
async def cmd_rating(message: Message, user: User | None) -> None:
    lang = user.language if user else "uz"
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start" if lang == "uz" else "❌ Сначала зарегистрируйтесь: /start")
        return
    rating = round(user.rating, 1) if user.rating else 0.0
    stars = "⭐" * int(rating) if rating >= 1 else "—"
    text = (
        f"⭐ <b>Sizning reytingiz</b>\n\nBaho: {rating}/5  {stars}\nJami deallar: {user.deal_count}"
        if lang == "uz" else
        f"⭐ <b>Ваш рейтинг</b>\n\nОценка: {rating}/5  {stars}\nВсего сделок: {user.deal_count}"
    )
    await message.answer(text, reply_markup=back_to_menu_keyboard(lang))


@router.message(Command("settings"))
async def cmd_settings(message: Message, user: User | None, state: FSMContext) -> None:
    await state.clear()
    lang = user.language if user else "uz"
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start" if lang == "uz" else "❌ Сначала зарегистрируйтесь: /start")
        return
    from bot.keyboards.inline import settings_keyboard
    await message.answer(t(lang, "SETTINGS_TITLE"), reply_markup=settings_keyboard(lang))


@router.message(Command("admin"))
async def cmd_admin_denied(message: Message, user: User | None) -> None:
    """Deny non-admin users from accessing /admin. The real handler is in admin.py."""
    from config import config as _cfg
    if message.from_user.id in _cfg.bot.admin_ids:
        return  # admin.py handler will take over
    lang = user.language if user else "uz"
    text = (
        "🚫 <b>Ruxsat yo'q!</b>\n\nBu buyruq faqat adminlar uchun."
        if lang == "uz" else
        "🚫 <b>Доступ запрещён!</b>\n\nЭта команда только для администраторов."
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Bosh menyu" if lang == "uz" else "🏠 Главное меню", callback_data="back:main")
    await message.answer(text, reply_markup=kb.as_markup())


# ─── FALLBACK FOR UNHANDLED MESSAGES ─────────────────────────

@router.message(StateFilter(None))
async def unknown_message(message: Message, user: User | None) -> None:
    lang = user.language if user else "uz"
    hint = (
        "🤔 Bu xabarni tushunmadim.\n\n"
        "Quyidagi buyruqlardan foydalaning:\n"
        "• /start — Botni ishga tushirish\n"
        "• /menu — Asosiy menyu\n"
        "• /my_orders — E'lonlarim\n"
        "• /rating — Reytingim\n"
        "• /help — Yordam\n"
        "• /settings — Sozlamalar"
        if lang == "uz" else
        "🤔 Я не понял это сообщение.\n\n"
        "Используйте команды:\n"
        "• /start — Запустить бота\n"
        "• /menu — Главное меню\n"
        "• /my_orders — Мои объявления\n"
        "• /rating — Мой рейтинг\n"
        "• /help — Помощь\n"
        "• /settings — Настройки"
    )
    await message.answer(hint, reply_markup=main_menu_keyboard(lang))
