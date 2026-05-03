"""
Kelishuv jarayoni handler — S-30..S-35
"""
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger
from sqlalchemy import update

from database import get_session, DealRepo, UserRepo, ListingRepo, ChatRepo
from database.models import User, DealStatus, ListingStatus, Deal
from locales import t
from bot.states.states import DealStates
from bot.keyboards.inline import (
    deal_start_chat_keyboard,
    deal_chat_keyboard, delivery_confirm_keyboard,
    rating_keyboard, back_to_menu_keyboard, complaint_reason_keyboard,
)
from bot.utils.notifications import (
    notify_sender_request_accepted,
    notify_sender_request_rejected,
    notify_deal_confirmed,
    notify_username_share_immediate,
)

router = Router(name="deal")


# ─── S-30: KURYER — QABUL/RAD ────────────────

@router.callback_query(F.data.startswith("deal_accept:"))
async def deal_accept(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    deal_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            await cb.answer("❌ Deal topilmadi")
            return
        await DealRepo.update_status(session, deal_id, DealStatus.negotiating)
        # Snapshot values inside session to avoid MissingGreenlet errors
        sender_id = deal.sender_id
        courier_id = deal.courier_id
        sender_lang = deal.sender.language if deal.sender else "uz"

    await notify_sender_request_accepted(cb.bot, sender_id, sender_lang)

    # Send chat intro to both parties
    from bot.keyboards.inline import deal_start_chat_keyboard
    for uid, ulang in [(sender_id, sender_lang), (courier_id, lang)]:
        await cb.bot.send_message(
            uid,
            t(ulang, "DEAL_CHAT_INTRO"),
            parse_mode="HTML",
            reply_markup=deal_start_chat_keyboard(ulang, deal_id),
        )

    await cb.message.edit_text(
        "✅ So'rov qabul qilindi! Chat boshlandi." if lang == "uz" else "✅ Запрос принят! Чат начался.",
        parse_mode="HTML",
    )
    await cb.answer()
    logger.info("✅ Deal qabul qilindi: deal_id={}", deal_id)


@router.callback_query(F.data.startswith("deal_reject:"))
async def deal_reject(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    deal_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            await cb.answer("❌ Deal topilmadi")
            return
        await DealRepo.update_status(session, deal_id, DealStatus.requested)
        # Snapshot before session closes
        sender_id = deal.sender_id
        sender_lang = deal.sender.language if deal.sender else "uz"

    await notify_sender_request_rejected(cb.bot, sender_id, sender_lang)
    await cb.message.edit_text(
        "❌ So'rov rad etildi." if lang == "uz" else "❌ Запрос отклонён.",
    )
    await cb.answer()
    logger.info("❌ Deal rad etildi: deal_id={}", deal_id)


# ─── S-31: BOT ICHIDA CHAT ───────────────────

@router.message(DealStates.chatting)
async def deal_chat_message(message: Message, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    data = await state.get_data()
    deal_id = data.get("deal_id")
    if not deal_id:
        return

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            return
        await ChatRepo.add_message(session, deal_id, user.id, message.text or "")
        other_id = deal.courier_id if user.id == deal.sender_id else deal.sender_id
        other_user = await UserRepo.get(session, other_id)
        other_lang = other_user.language if other_user else "uz"

    sender_name = user.full_name.split()[0]
    fwd_text = f"💬 <b>{sender_name}:</b>\n{message.text}"
    await message.bot.send_message(
        other_id, fwd_text, parse_mode="HTML",
        reply_markup=deal_chat_keyboard(other_lang, deal_id),
    )


# ─── S-31: KELISHDIM TUGMASI ─────────────────

@router.callback_query(F.data.startswith("deal_confirm:"))
async def deal_confirm(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    deal_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            await cb.answer("❌ Deal topilmadi")
            return

        is_sender = user.id == deal.sender_id
        field = "sender_confirmed" if is_sender else "courier_confirmed"
        await session.execute(update(Deal).where(Deal.id == deal_id).values(**{field: True}))
        await session.flush()
        deal = await DealRepo.get(session, deal_id)
        both_confirmed = deal.sender_confirmed and deal.courier_confirmed
        listing = deal.listing

    confirmed_text = (
        "✅ Siz kelishdingiz! Ikkinchi tomon kelishishini kutayapmiz..."
        if lang == "uz" else
        "✅ Вы договорились! Ожидаем второй стороны..."
    )
    await cb.answer(confirmed_text, show_alert=True)

    if both_confirmed:
        async with get_session() as session:
            await DealRepo.update_status(session, deal_id, DealStatus.confirmed)
            deal = await DealRepo.get(session, deal_id)
            # Snapshot data before session closes to avoid lazy-load errors
            sender_lang_snap = deal.sender.language if deal.sender else "uz"
            courier_lang_snap = deal.courier.language if deal.courier else "uz"
            sender_id_snap = deal.sender_id
            courier_id_snap = deal.courier_id

        for uid, ulang in [
            (sender_id_snap, sender_lang_snap),
            (courier_id_snap, courier_lang_snap),
        ]:
            await notify_deal_confirmed(
                cb.bot, uid, ulang,
                listing.from_city,
                listing.flight_date.strftime("%d.%m.%Y"),
                listing.flight_time,
            )

        # Darhol username almashish — deal tasdiqlangandan so'ng!
        async with get_session() as session:
            fresh_deal = await DealRepo.get(session, deal_id)
            await notify_username_share_immediate(cb.bot, fresh_deal)

        logger.info("🤝 Deal tasdiqlandi: deal_id={}", deal_id)


@router.callback_query(F.data.startswith("deal_cancel:"))
async def deal_cancel(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    deal_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            await cb.answer("❌")
            return
        await DealRepo.update_status(session, deal_id, DealStatus.requested)
        other_id = deal.courier_id if user.id == deal.sender_id else deal.sender_id
        other_user = await UserRepo.get(session, other_id)
        other_lang = other_user.language if other_user else "uz"

    cancel_msg = "❌ Kelishuv bekor qilindi." if lang == "uz" else "❌ Договорённость отменена."
    await cb.bot.send_message(other_id, cancel_msg)
    await cb.message.edit_text(cancel_msg)
    await state.clear()
    await cb.answer()


# ─── S-34: YETKAZILDI TASDIQLASH ─────────────

@router.callback_query(F.data.startswith("delivery_confirm:"))
async def delivery_confirm(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    parts = cb.data.split(":")
    deal_id = int(parts[1])
    is_sender = parts[2] == "sender"

    async with get_session() as session:
        deal = await DealRepo.confirm_delivery(session, deal_id, is_sender)
        both = deal.sender_confirmed and deal.courier_confirmed
        if both:
            await DealRepo.update_status(session, deal_id, DealStatus.completed)
            await session.execute(
                update(Deal).where(Deal.id == deal_id).values(completed_at=datetime.now(timezone.utc))
            )
            await ListingRepo.update_status(session, deal.listing_id, ListingStatus.completed)

    if both:
        # Languages were eager-loaded inside the session via DealRepo.confirm_delivery
        # We access scalar IDs only (safe), language needs special handling
        sender_lang_d = deal.sender.language if deal.sender else "uz"
        courier_lang_d = deal.courier.language if deal.courier else "uz"
        for uid, ulang in [
            (deal.sender_id, sender_lang_d),
            (deal.courier_id, courier_lang_d),
        ]:
            await cb.bot.send_message(
                uid, t(ulang, "DEAL_COMPLETED"),
                reply_markup=rating_keyboard(ulang, deal_id),
                parse_mode="HTML",
            )
        logger.info("🎉 Deal yakunlandi: deal_id={}", deal_id)
    else:
        wait_msg = (
            "✅ Siz tasdiqladingiz. Ikkinchi tomon tasdiqlashini kutayapmiz..."
            if lang == "uz" else
            "✅ Вы подтвердили. Ожидаем подтверждения второй стороны..."
        )
        await cb.answer(wait_msg, show_alert=True)


@router.callback_query(F.data.startswith("delivery_problem:"))
async def delivery_problem(cb: CallbackQuery, user: User | None) -> None:
    lang = user.language if user else "uz"
    await cb.message.edit_text(
        t(lang, "COMPLAINT_REASON"),
        reply_markup=complaint_reason_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()


# ─── S-35: BAHO BERISH ───────────────────────

@router.callback_query(F.data.startswith("rate:"))
async def rate_deal(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    parts = cb.data.split(":")
    deal_id = int(parts[1])
    rating = int(parts[2])

    async with get_session() as session:
        deal = await DealRepo.get(session, deal_id)
        if not deal:
            await cb.answer("❌")
            return
        is_sender = user.id == deal.sender_id
        await DealRepo.set_rating(session, deal_id, is_sender, rating)

        rated_user_id = deal.courier_id if is_sender else deal.sender_id
        rated_user = await UserRepo.get(session, rated_user_id)
        old_rating = rated_user.rating or 0.0
        old_count = rated_user.deal_count or 0
        new_count = old_count + 1
        new_rating = ((old_rating * old_count) + rating) / new_count
        await UserRepo.update(session, rated_user_id, rating=round(new_rating, 2), deal_count=new_count)

    stars = "⭐" * rating
    thanks = f"Rahmat! {stars} baho berdingiz 🙏" if lang == "uz" else f"Спасибо! Вы поставили {stars} 🙏"
    await cb.message.edit_text(
        thanks + "\n\n" + t(lang, "MAIN_MENU"),
        reply_markup=back_to_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await cb.answer()
    logger.info("⭐ Baho berildi: deal_id={} rating={} by={}", deal_id, rating, user.id)


# ─── CHAT BOSHLASH ───────────────────────────

@router.callback_query(F.data.startswith("start_chat:"))
async def start_chat(cb: CallbackQuery, user: User | None, state: FSMContext) -> None:
    lang = user.language if user else "uz"
    deal_id = int(cb.data.split(":")[1])
    await state.set_state(DealStates.chatting)
    await state.update_data(deal_id=deal_id)

    chat_hint = (
        "💬 <b>Chat boshlandi!</b>\n\nXabar yozing — ikkinchi tomonga yetkaziladi.\nKelishsangiz ✅ Kelishdim tugmasini bosing."
        if lang == "uz" else
        "💬 <b>Чат начался!</b>\n\nНапишите сообщение — оно будет передано второй стороне.\nЕсли договорились, нажмите ✅ Договорились."
    )
    await cb.message.edit_text(
        chat_hint,
        reply_markup=deal_chat_keyboard(lang, deal_id),
        parse_mode="HTML",
    )
    await cb.answer()
    logger.info("💬 Chat boshlandi: deal_id={} user_id={}", deal_id, user.id if user else "?")
