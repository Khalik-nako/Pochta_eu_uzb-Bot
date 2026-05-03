"""
Admin panel — video approval, complaints, blocks, broadcast.
Only accessible to users listed in ADMIN_IDS.
"""
from datetime import datetime, timezone as _tz

from aiogram import Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy import update, select
from sqlalchemy.orm import selectinload

from database import get_session, UserRepo, ListingRepo, DealRepo, ComplaintRepo, BlacklistRepo, SubscriptionRepo, TaxiRepo, UserStatsRepo
from database.models import User, ListingStatus, ComplaintStatus, BlockType, CourierListing, Complaint, TaxiService
from bot.states.states import AdminStates
from bot.keyboards.inline import (
    admin_main_keyboard, admin_verify_keyboard, admin_reject_reason_keyboard,
    admin_complaint_keyboard, admin_broadcast_keyboard, back_to_menu_keyboard,
    admin_contact_keyboard, admin_taxi_keyboard, admin_taxi_list_keyboard,
    admin_listing_manage_keyboard, admin_broadcast_countries_keyboard,
)
from bot.utils.notifications import (
    notify_listing_approved, notify_listing_rejected,
    notify_admins, notify_subscription_match,
)
from config import config

router = Router(name="admin")


class AdminFilter(BaseFilter):
    async def __call__(self, obj: TelegramObject, event_from_user=None, **data) -> bool:
        if not event_from_user:
            return False
        return event_from_user.id in config.bot.admin_ids


router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


def _admin_panel_text(pending: int, complaints: int, active: int, new_users: int) -> str:
    now = datetime.now(_tz.utc).strftime("%H:%M")
    return (
        f"🛠 <b>Admin panel</b>  <code>{now} UTC</code>\n\n"
        f"⏳ Tasdiqlash kutayotganlar: <b>{pending}</b>\n"
        f"🚨 Yangi shikoyatlar: <b>{complaints}</b>\n"
        f"📋 Faol e'lonlar: <b>{active}</b>\n"
        f"👤 Bugungi yangi foydalanuvchilar: <b>{new_users}</b>"
    )


# ─── A-01: ADMIN PANEL ───────────────────────────────────────

@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    async with get_session() as session:
        pending = len(await ListingRepo.get_pending(session))
        complaints = await ComplaintRepo.count_new(session)
        active = await ListingRepo.count_active(session)
        new_users = await UserRepo.count_new_today(session)

    text = _admin_panel_text(pending, complaints, active, new_users)
    await message.answer(text, reply_markup=admin_main_keyboard())


@router.callback_query(F.data == "admin:main")
async def admin_main_cb(cb: CallbackQuery) -> None:
    async with get_session() as session:
        pending = len(await ListingRepo.get_pending(session))
        complaints = await ComplaintRepo.count_new(session)
        active = await ListingRepo.count_active(session)
        new_users = await UserRepo.count_new_today(session)

    text = _admin_panel_text(pending, complaints, active, new_users)
    await cb.message.edit_text(text, reply_markup=admin_main_keyboard())
    await cb.answer()


# ─── A-02: COURIER VERIFICATION ──────────────────────────────

@router.callback_query(F.data == "admin:verify")
async def admin_verify_list(cb: CallbackQuery) -> None:
    async with get_session() as session:
        listings = await ListingRepo.get_pending(session)
        listing_data = []
        for listing in listings[:5]:
            user = listing.user
            listing_data.append({
                "id": listing.id,
                "full_name": user.full_name if user else "—",
                "phone": user.phone if user else "—",
                "country": user.country if user else "—",
                "from_city": listing.from_city,
                "flight_date": listing.flight_date.strftime("%d.%m.%Y"),
                "flight_time": listing.flight_time,
                "max_kg": listing.max_kg,
                "price_per_kg": listing.price_per_kg,
                "restrictions": ", ".join(listing.restrictions or []) or "—",
                "video_msg_id": listing.video_msg_id or "—",
            })

    if not listing_data:
        await cb.answer("✅ Hozircha yangi so'rovlar yo'q", show_alert=True)
        return

    for d in listing_data:
        text = (
            f"🆕 <b>Yangi so'rov #{d['id']}</b>\n\n"
            f"👤 Ism: {d['full_name']}\n"
            f"📱 Telefon: {d['phone']}\n"
            f"🌍 Davlat: {d['country']}\n"
            f"📍 Yo'nalish: {d['from_city']} → Toshkent\n"
            f"📅 Sana: {d['flight_date']} · {d['flight_time']}\n"
            f"⚖️ Max yuk: {d['max_kg']} kg\n"
            f"💶 Narx: €{d['price_per_kg']}/kg\n"
            f"🚫 Olmaydi: {d['restrictions']}\n"
            f"🎥 Video msg_id: {d['video_msg_id']}\n\n"
            f"⚠️ <b>Tasdiqlash yoki rad eting:</b>"
        )
        await cb.message.answer(text, reply_markup=admin_verify_keyboard(d["id"]))
    await cb.answer()


@router.callback_query(F.data.startswith("admin_video:"))
async def admin_view_video(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)

    if not listing or not listing.video_msg_id:
        await cb.answer("❌ Video topilmadi", show_alert=True)
        return

    try:
        await cb.bot.forward_message(
            chat_id=cb.from_user.id,
            from_chat_id=config.channel.video_channel_id,
            message_id=int(listing.video_msg_id),
        )
        await cb.answer("📹 Video yuborildi")
    except Exception as e:
        await cb.answer(f"❌ Video topilmadi: {e}", show_alert=True)


@router.callback_query(F.data.startswith("admin_approve:"))
async def admin_approve(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[1])

    # Collect all needed data inside one session to avoid lazy-load issues
    async with get_session() as session:
        result = await session.execute(
            select(CourierListing)
            .options(selectinload(CourierListing.user))
            .where(CourierListing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing:
            await cb.answer("❌ E'lon topilmadi", show_alert=True)
            return
        if not listing.user:
            await cb.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
            return

        await ListingRepo.update_status(session, listing_id, ListingStatus.active)
        await session.execute(
            update(CourierListing)
            .where(CourierListing.id == listing_id)
            .values(is_verified=True, age_verified=True)
        )

        # Snapshot needed values before session closes
        user_id = listing.user.id
        user_lang = listing.user.language
        user_country = listing.user.country
        from_city = listing.from_city
        flight_date_str = listing.flight_date.strftime("%d.%m.%Y")
        flight_time = listing.flight_time
        max_kg = listing.max_kg
        price_per_kg = listing.price_per_kg

        month_str = f"{listing.flight_date.year}-{listing.flight_date.month:02d}"
        subs = await SubscriptionRepo.get_subscribers(session, user_country, month_str)
        sub_data = []
        for sub in subs:
            sub_user = await UserRepo.get(session, sub.user_id)
            sub_data.append((sub.user_id, sub_user.language if sub_user else "uz"))

    await notify_listing_approved(
        cb.bot,
        user_id=user_id,
        lang=user_lang,
        city=from_city,
        date=flight_date_str,
        time=flight_time,
        max_kg=max_kg,
        price=price_per_kg,
    )

    for sub_uid, sub_lang in sub_data:
        await notify_subscription_match(cb.bot, sub_uid, sub_lang)

    await cb.message.edit_text(f"✅ Listing #{listing_id} tasdiqlandi!\nKuryerga xabar yuborildi.")
    await cb.answer("✅ Tasdiqlandi")
    logger.info("Admin approved listing: {}", listing_id)


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(cb: CallbackQuery, state: FSMContext) -> None:
    listing_id = int(cb.data.split(":")[1])
    await state.update_data(reject_listing_id=listing_id)
    await cb.message.edit_text(
        "❌ Rad etish sababini tanlang:",
        reply_markup=admin_reject_reason_keyboard(listing_id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("reject_reason:"))
async def admin_reject_reason(cb: CallbackQuery, state: FSMContext) -> None:
    parts = cb.data.split(":")
    listing_id = int(parts[1])
    reason_key = parts[2]

    reason_map = {
        "face": "Yuz aniq ko'rinmagan",
        "passport": "Pasport ko'rinmaydi",
        "name": "Ism mos emas",
        "quality": "Video sifatsiz",
        "age": "18 yoshdan kichik",
    }
    reason_text = reason_map.get(reason_key, "Noma'lum sabab")

    async with get_session() as session:
        result = await session.execute(
            select(CourierListing)
            .options(selectinload(CourierListing.user))
            .where(CourierListing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing or not listing.user:
            await cb.answer("❌ Topilmadi", show_alert=True)
            return

        user_id = listing.user.id
        user_lang = listing.user.language
        await ListingRepo.update_status(session, listing_id, ListingStatus.pending)

    from locales import t
    await notify_listing_rejected(cb.bot, user_id, user_lang, reason_text)

    if reason_key == "age":
        age_msg = t(user_lang, "AGE_RESTRICTED")
        await cb.bot.send_message(
            user_id, age_msg,
            reply_markup=admin_contact_keyboard(user_lang),
        )

    await cb.message.edit_text(f"❌ Listing #{listing_id} rad etildi.\nSabab: {reason_text}")
    await cb.answer("❌ Rad etildi")
    logger.info("Admin rejected listing: {} reason: {}", listing_id, reason_key)


@router.callback_query(F.data.startswith("admin_revideo:"))
async def admin_request_revideo(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[1])

    async with get_session() as session:
        result = await session.execute(
            select(CourierListing)
            .options(selectinload(CourierListing.user))
            .where(CourierListing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing or not listing.user:
            await cb.answer("❌ Topilmadi", show_alert=True)
            return

        # Snapshot before session closes
        user_id = listing.user.id
        user_lang = listing.user.language

    from locales import t
    from bot.keyboards.inline import nav_keyboard
    msg = "🎥 Admin sizdan qayta video yuborishingizni so'raydi.\n\n" + t(user_lang, "SEND_VERIFICATION_VIDEO")
    await cb.bot.send_message(user_id, msg, reply_markup=nav_keyboard(user_lang, "back:main"))
    await cb.answer("📩 So'rov yuborildi")


# ─── A-03: COMPLAINTS ────────────────────────────────────────

@router.callback_query(F.data == "admin:complaints")
async def admin_complaints(cb: CallbackQuery) -> None:
    async with get_session() as session:
        complaints = await ComplaintRepo.get_new(session)

    if not complaints:
        await cb.answer("✅ Yangi shikoyatlar yo'q", show_alert=True)
        return

    for c in complaints[:5]:
        from_name = c.from_user.full_name if c.from_user else "—"
        against_name = c.against_user.full_name if c.against_user else "—"
        text = (
            f"🚨 <b>Shikoyat #{c.id}</b>\n\n"
            f"Kim: {from_name}\n"
            f"Kimga: {against_name}\n"
            f"Sabab: {c.reason}\n"
            f"Sana: {c.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await cb.message.answer(text, reply_markup=admin_complaint_keyboard(c.id, c.against_id))
    await cb.answer()


@router.callback_query(F.data.startswith("complaint_resolve:"))
async def complaint_resolve(cb: CallbackQuery) -> None:
    complaint_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        await ComplaintRepo.update_status(session, complaint_id, ComplaintStatus.resolved)
    await cb.message.edit_text(f"✅ Shikoyat #{complaint_id} hal qilindi.")
    await cb.answer("✅")


@router.callback_query(F.data.startswith("complaint_archive:"))
async def complaint_archive(cb: CallbackQuery) -> None:
    complaint_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        await ComplaintRepo.update_status(session, complaint_id, ComplaintStatus.closed)
    await cb.message.edit_text(f"📁 Shikoyat #{complaint_id} arxivlandi.")
    await cb.answer()


@router.callback_query(F.data.startswith("admin_chat:"))
async def admin_chat_both(cb: CallbackQuery) -> None:
    complaint_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        result = await session.execute(select(Complaint).where(Complaint.id == complaint_id))
        complaint = result.scalar_one_or_none()

    if not complaint:
        await cb.answer("❌ Shikoyat topilmadi")
        return

    msg = f"ℹ️ #{complaint_id} shikoyat ko'rib chiqilmoqda. Adminlar bilan bog'laning."
    for uid in [complaint.from_id, complaint.against_id]:
        try:
            await cb.bot.send_message(uid, msg)
        except Exception:
            pass
    await cb.answer("📩 Xabar yuborildi")


# ─── A-04: USER BLOCKING ─────────────────────────────────────

@router.callback_query(F.data == "admin:block")
async def admin_block_menu(cb: CallbackQuery) -> None:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 User ID bo'yicha qidirish", callback_data="admin_block_search")
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    kb.adjust(1)
    await cb.message.edit_text("🚫 <b>Bloklash</b>\n\nUser ID kiriting yoki shikoyatdan bloklang:", reply_markup=kb.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("admin_block:"))
async def admin_block_user(cb: CallbackQuery) -> None:
    user_id = int(cb.data.split(":")[1])
    kb = InlineKeyboardBuilder()
    kb.button(text="⚠️ Ogohlantirish", callback_data=f"block_warn:{user_id}")
    kb.button(text="🔴 Vaqtinchalik", callback_data=f"block_temp:{user_id}")
    kb.button(text="⚫ Doimiy", callback_data=f"block_perm:{user_id}")
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    kb.adjust(1)
    await cb.message.edit_text(f"🚫 Foydalanuvchi #{user_id} uchun amal tanlang:", reply_markup=kb.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("block_warn:"))
async def block_warn(cb: CallbackQuery) -> None:
    user_id = int(cb.data.split(":")[1])
    try:
        await cb.bot.send_message(user_id, "⚠️ Admin ogohlantirishini oldingiz. Qoidalarga rioya qiling.")
    except Exception:
        pass
    await cb.answer("⚠️ Ogohlantirish yuborildi")


@router.callback_query(F.data.startswith("block_temp:"))
async def block_temp(cb: CallbackQuery) -> None:
    user_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        await UserRepo.update(session, user_id, is_blocked=True, block_type=BlockType.temp)
        db_user = await UserRepo.get(session, user_id)
        if db_user:
            from database import BlacklistRepo
            await BlacklistRepo.add(
                session, phone=db_user.phone, telegram_id=user_id,
                reason="Admin: vaqtinchalik blok", is_permanent=False,
            )
    try:
        await cb.bot.send_message(user_id, "🔴 Akkauntingiz vaqtinchalik bloklandi.")
    except Exception:
        pass
    await cb.message.edit_text(f"🔴 #{user_id} vaqtinchalik bloklandi.")
    await cb.answer()
    logger.warning("Temp block: user_id={}", user_id)


@router.callback_query(F.data.startswith("block_perm:"))
async def block_perm(cb: CallbackQuery) -> None:
    user_id = int(cb.data.split(":")[1])
    async with get_session() as session:
        await UserRepo.update(session, user_id, is_blocked=True, block_type=BlockType.permanent)
        db_user = await UserRepo.get(session, user_id)
        if db_user:
            from database import BlacklistRepo
            await BlacklistRepo.add(
                session, phone=db_user.phone, telegram_id=user_id,
                reason="Admin: doimiy blok", is_permanent=True,
            )
    try:
        await cb.bot.send_message(user_id, "⚫ Akkauntingiz doimiy bloklandi.")
    except Exception:
        pass
    await cb.message.edit_text(f"⚫ #{user_id} doimiy bloklandi.")
    await cb.answer()
    logger.warning("Permanent block: user_id={}", user_id)


# ─── A-05: STATISTICS ────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery) -> None:
    async with get_session() as session:
        new_users = await UserRepo.count_new_today(session)
        active_listings = await ListingRepo.count_active(session)
        completed_today = await DealRepo.count_completed_today(session)
        complaint_count = await ComplaintRepo.count_new(session)
        country_stats = await UserStatsRepo.count_by_country(session)

    # Davlatlar bo'yicha statistika
    country_lines = ""
    total_users = sum(country_stats.values())
    for country, count in list(country_stats.items())[:10]:
        bar = "▓" * min(count, 10) + "░" * max(0, 10 - count)
        country_lines += f"\n  {bar} {country}: <b>{count}</b>"

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"<b>Bugun:</b>\n"
        f"  👤 Yangi foydalanuvchilar: {new_users}\n"
        f"  🤝 Tugallangan deallar: {completed_today}\n\n"
        f"<b>Jami:</b>\n"
        f"  📋 Faol e'lonlar: {active_listings}\n"
        f"  🚨 Ko'rilmagan shikoyatlar: {complaint_count}\n"
        f"  👥 Jami foydalanuvchilar: {total_users}\n\n"
        f"<b>🌍 Davlatlar bo'yicha:</b>{country_lines}"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    await cb.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()


# ─── A-04: ACTIVE LISTINGS OVERVIEW ─────────────────────────

@router.callback_query(F.data == "admin:listings")
async def admin_listings(cb: CallbackQuery) -> None:
    async with get_session() as session:
        pending_listings = await ListingRepo.get_pending(session)
        active_count = await ListingRepo.count_active(session)
        result = await session.execute(
            select(CourierListing)
            .options(selectinload(CourierListing.user))
            .where(CourierListing.status == ListingStatus.active)
            .order_by(CourierListing.created_at.desc())
            .limit(10)
        )
        active_listings = result.scalars().all()
        active_data = [
            {
                "id": l.id,
                "name": l.user.full_name if l.user else "—",
                "city": l.from_city,
                "date": l.flight_date.strftime("%d.%m.%Y"),
                "is_pinned": getattr(l, "is_pinned", False),
                "has_diamond": getattr(l, "has_diamond", False),
            }
            for l in active_listings
        ]

    if active_data:
        lines = ""
        for d in active_data:
            pin = "📌 " if d.get("is_pinned") else ""
            diamond = "💎 " if d.get("has_diamond") else ""
            lines += f"\n{pin}{diamond}#{d['id']} <b>{d['name']}</b> · {d['city']} · {d['date']}"
    else:
        lines = "\nFaol e'lonlar yo'q"

    text = (
        f"📋 <b>Faol e'lonlar: {active_count}</b>\n"
        f"⏳ Tasdiqlash kutayotganlar: <b>{len(pending_listings)}</b>\n"
        + lines
        + "\n\n🔧 Boshqarish uchun quyidagi tugmalardan tanlang:"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Kutayotganlarni ko'rish", callback_data="admin:verify")
    kb.button(text="🔄 Yangilash", callback_data="admin:listings")
    for d in active_data[:5]:
        pin = "📌" if d.get("is_pinned") else "📄"
        kb.button(text=f"{pin} #{d['id']} — {d['name']}", callback_data=f"admin_listing:manage:{d['id']}")
    kb.button(text="⬅️ Orqaga", callback_data="admin:main")
    kb.adjust(2, *([1] * min(len(active_data), 5)), 1)

    await cb.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()


# ─── A-06: BROADCAST ─────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.broadcast_target)
    await cb.message.edit_text("📣 <b>Kimga xabar yuboramiz?</b>", reply_markup=admin_broadcast_keyboard(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("broadcast:countries_page:"))
async def broadcast_countries_page(cb: CallbackQuery) -> None:
    page = int(cb.data.split(":")[-1])
    await cb.message.edit_text("🌍 Davlatni tanlang:", reply_markup=admin_broadcast_countries_keyboard(page))
    await cb.answer()


@router.callback_query(F.data == "broadcast:more_countries")
async def broadcast_more_countries(cb: CallbackQuery) -> None:
    await cb.message.edit_text("🌍 Barcha davlatlar:", reply_markup=admin_broadcast_countries_keyboard(0))
    await cb.answer()


@router.callback_query(AdminStates.broadcast_target, F.data.startswith("broadcast:"))
async def broadcast_select_target(cb: CallbackQuery, state: FSMContext) -> None:
    target = cb.data.split(":", 1)[1]
    await state.update_data(broadcast_target=target)
    await state.set_state(AdminStates.broadcast_text)
    await cb.message.edit_text("📝 Xabar matnini yozing:")
    await cb.answer()


@router.message(AdminStates.broadcast_text)
async def broadcast_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target = data.get("broadcast_target", "all")
    text = message.text or ""

    target_labels = {
        "all": "Barcha foydalanuvchilar",
        "couriers": "Faqat kuryrlar",
        "senders": "Faqat jo'natuvchilar",
    }
    label = target_labels.get(target, target)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yuborish", callback_data="broadcast_send")
    kb.button(text="✏️ Tahrirlash", callback_data="broadcast_edit")
    kb.button(text="❌ Bekor qilish", callback_data="admin:main")
    kb.adjust(1)

    await state.update_data(broadcast_text=text)
    await message.answer(
        f"📣 <b>Xabar ko'rib chiqish:</b>\n\nKimga: {label}\n\n<blockquote>{text}</blockquote>",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    target = data.get("broadcast_target", "all")

    async with get_session() as session:
        if target == "all":
            users = await UserRepo.get_all(session)
        elif target == "couriers":
            # Kuryer e'loni bo'lganlar
            from sqlalchemy import select as _sel
            result = await session.execute(
                _sel(User).join(CourierListing, CourierListing.user_id == User.id).distinct()
            )
            users = list(result.scalars().all())
        elif target.startswith("country:"):
            country = target.split(":", 1)[1]
            users = await UserStatsRepo.get_by_country(session, country)
        else:
            users = await UserRepo.get_all(session)

    sent, failed = 0, 0
    for u in users:
        try:
            await cb.bot.send_message(u.id, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    target_label = target if not target.startswith("country:") else f"🌍 {target.split(':', 1)[1]}"
    await cb.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"Kimga: {target_label}\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )
    await cb.answer()
    logger.info("Broadcast done: sent={} failed={} target={}", sent, failed, target)


@router.callback_query(F.data == "broadcast_edit")
async def broadcast_edit(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.broadcast_text)
    await cb.message.edit_text("📝 Yangi xabar matnini yozing:")
    await cb.answer()


# ─── A-07: FAOL E'LONLARNI BOSHQARISH ───────────────────────

@router.callback_query(F.data.startswith("admin_listing:manage:"))
async def admin_listing_manage(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)

    if not listing:
        await cb.answer("❌ E'lon topilmadi", show_alert=True)
        return

    user_name = listing.user.full_name if listing.user else "—"
    is_pinned = getattr(listing, "is_pinned", False)
    has_diamond = getattr(listing, "has_diamond", False)

    pin_badge = "📌 " if is_pinned else ""
    diamond_badge = "💎 " if has_diamond else ""

    text = (
        f"{pin_badge}{diamond_badge}<b>E'lon #{listing_id}</b>\n\n"
        f"👤 Kuryer: {user_name}\n"
        f"📍 Shahar: {listing.from_city}\n"
        f"📅 Sana: {listing.flight_date.strftime('%d.%m.%Y')} · {listing.flight_time}\n"
        f"⚖️ Max: {listing.max_kg} kg\n"
        f"💶 Narx: €{listing.price_per_kg}/kg\n"
        f"📊 Status: {listing.status.value}"
    )
    await cb.message.edit_text(
        text,
        reply_markup=admin_listing_manage_keyboard(listing_id, is_pinned),
        parse_mode="HTML",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_listing:pin:"))
async def admin_listing_pin(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)
        if not listing:
            await cb.answer("❌ Topilmadi", show_alert=True)
            return
        new_pin = not getattr(listing, "is_pinned", False)
        from sqlalchemy import update as _upd
        await session.execute(
            _upd(CourierListing).where(CourierListing.id == listing_id).values(is_pinned=new_pin)
        )

    action = "📌 Tepaga pinlandi!" if new_pin else "📌 Pindan olib tashlandi!"
    await cb.answer(action, show_alert=True)
    # Refresh
    await cb.message.edit_reply_markup(reply_markup=admin_listing_manage_keyboard(listing_id, new_pin))
    logger.info("Admin listing pin: id={} pinned={}", listing_id, new_pin)


@router.callback_query(F.data.startswith("admin_listing:diamond:"))
async def admin_listing_diamond(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)
        if not listing:
            await cb.answer("❌ Topilmadi", show_alert=True)
            return
        current = getattr(listing, "has_diamond", False)
        from sqlalchemy import update as _upd
        await session.execute(
            _upd(CourierListing).where(CourierListing.id == listing_id).values(has_diamond=not current)
        )
        user_id = listing.user_id
        user_lang = listing.user.language if listing.user else "uz"

    # Kuryerga xabar
    if not current:
        try:
            diamond_msg = (
                "💎 <b>Tabriklaymiz!</b>\n\nAdmin sizning e'loningizga Diamond belgisi berdi. "
                "Bu sizning ishonchli kuryer ekanligingizni bildiradi! ✨"
                if user_lang == "uz" else
                "💎 <b>Поздравляем!</b>\n\nАдминистратор присвоил вашему объявлению Diamond-статус. "
                "Это означает, что вы проверенный курьер! ✨"
            )
            await cb.bot.send_message(user_id, diamond_msg, parse_mode="HTML")
        except Exception:
            pass

    action = "💎 Diamond berildi!" if not current else "💎 Diamond olib tashlandi"
    await cb.answer(action, show_alert=True)
    logger.info("Admin listing diamond: id={} diamond={}", listing_id, not current)


@router.callback_query(F.data.startswith("admin_listing:edit:"))
async def admin_listing_edit(cb: CallbackQuery, state: FSMContext) -> None:
    listing_id = int(cb.data.split(":")[-1])
    await state.update_data(edit_listing_id=listing_id)
    await state.set_state(AdminStates.listing_edit_value)

    kb = InlineKeyboardBuilder()
    kb.button(text="💶 Narx/kg o'zgartirish", callback_data=f"listing_edit_field:price:{listing_id}")
    kb.button(text="⚖️ Max kg o'zgartirish", callback_data=f"listing_edit_field:kg:{listing_id}")
    kb.button(text="⬅️ Orqaga", callback_data=f"admin_listing:manage:{listing_id}")
    kb.adjust(1)
    await cb.message.edit_text("✏️ Nima o'zgartirmoqchisiz?", reply_markup=kb.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("listing_edit_field:"))
async def listing_edit_field_select(cb: CallbackQuery, state: FSMContext) -> None:
    parts = cb.data.split(":")
    field = parts[1]
    listing_id = int(parts[2])
    await state.update_data(edit_listing_id=listing_id, edit_field=field)

    label = "💶 Yangi narx (€/kg) kiriting:" if field == "price" else "⚖️ Yangi max kg kiriting:"
    await cb.message.edit_text(label)
    await cb.answer()


@router.message(AdminStates.listing_edit_value)
async def listing_edit_value_enter(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    listing_id = data.get("edit_listing_id")
    field = data.get("edit_field", "price")

    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting.")
        return

    from sqlalchemy import update as _upd
    field_map = {"price": "price_per_kg", "kg": "max_kg"}
    db_field = field_map.get(field, "price_per_kg")

    async with get_session() as session:
        await session.execute(
            _upd(CourierListing).where(CourierListing.id == listing_id).values(**{db_field: value})
        )
        listing = await ListingRepo.get(session, listing_id)
        user_id = listing.user_id if listing else None
        user_lang = listing.user.language if listing and listing.user else "uz"

    # Kuryerga xabar
    if user_id:
        try:
            upd_msg = (
                f"📝 <b>E'loningiz yangilandi</b>\n\nAdmin tomonidan: {db_field.replace('_', ' ')} = {value}"
                if user_lang == "uz" else
                f"📝 <b>Объявление обновлено</b>\n\nАдминистратором: {db_field.replace('_', ' ')} = {value}"
            )
            await message.bot.send_message(user_id, upd_msg, parse_mode="HTML")
        except Exception:
            pass

    await state.clear()
    await message.answer(
        f"✅ E'lon #{listing_id} yangilandi: {db_field} = {value}",
        reply_markup=admin_listing_manage_keyboard(listing_id, False)
    )
    logger.info("Admin listing edit: id={} field={} value={}", listing_id, db_field, value)


@router.callback_query(F.data.startswith("admin_listing:delete:"))
async def admin_listing_delete(cb: CallbackQuery) -> None:
    listing_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        listing = await ListingRepo.get(session, listing_id)
        if not listing:
            await cb.answer("❌ Topilmadi", show_alert=True)
            return
        user_id = listing.user_id
        user_lang = listing.user.language if listing.user else "uz"
        await ListingRepo.update_status(session, listing_id, ListingStatus.deleted)

    # Kuryerga xabar
    try:
        del_msg = (
            "🗑 <b>E'loningiz o'chirildi</b>\n\nAdmin tomonidan e'loningiz olib tashlandi."
            if user_lang == "uz" else
            "🗑 <b>Ваше объявление удалено</b>\n\nОбъявление удалено администратором."
        )
        await cb.bot.send_message(user_id, del_msg, parse_mode="HTML")
    except Exception:
        pass

    await cb.message.edit_text(f"🗑 E'lon #{listing_id} o'chirildi.")
    await cb.answer("✅ O'chirildi")
    logger.info("Admin deleted listing: {}", listing_id)


# ─── A-08: TAXI BOSHQARISH ───────────────────────────────────

@router.callback_query(F.data == "admin:taxi")
async def admin_taxi_list(cb: CallbackQuery) -> None:
    async with get_session() as session:
        taxis = await TaxiRepo.get_all_active(session)

    if not taxis:
        kb = InlineKeyboardBuilder()
        kb.button(text="➕ Yangi taxi qo'shish", callback_data="admin_taxi:add")
        kb.button(text="⬅️ Orqaga", callback_data="admin:main")
        kb.adjust(1)
        await cb.message.edit_text(
            "🚕 <b>Taxi xizmatlari</b>\n\nHozircha taxi xizmatlari yo'q.",
            reply_markup=kb.as_markup(), parse_mode="HTML"
        )
    else:
        count = len(taxis)
        await cb.message.edit_text(
            f"🚕 <b>Taxi xizmatlari ({count} ta)</b>\n\nBoshqarish uchun tanlang:",
            reply_markup=admin_taxi_list_keyboard(taxis), parse_mode="HTML"
        )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_taxi:manage:"))
async def admin_taxi_manage(cb: CallbackQuery) -> None:
    taxi_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        taxi = await TaxiRepo.get(session, taxi_id)

    if not taxi:
        await cb.answer("❌ Topilmadi", show_alert=True)
        return

    driver_name = taxi.driver.full_name if taxi.driver else "—"
    pin_icon = "📌 " if taxi.is_pinned else ""
    text = (
        f"{pin_icon}🚕 <b>Taxi #{taxi.id}</b>\n\n"
        f"👤 Haydovchi: {driver_name}\n"
        f"🌍 Davlatlar: {taxi.countries}\n"
        f"📦 Yuklar: {taxi.cargo_types}\n"
        f"👥 Sig'im: {taxi.passenger_capacity} kishi\n"
        f"📝 Tavsif: {taxi.description or '—'}"
    )
    await cb.message.edit_text(text, reply_markup=admin_taxi_keyboard(taxi_id), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("admin_taxi:pin:"))
async def admin_taxi_pin(cb: CallbackQuery) -> None:
    taxi_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        taxi = await TaxiRepo.get(session, taxi_id)
        if not taxi:
            await cb.answer("❌", show_alert=True)
            return
        new_pin = not taxi.is_pinned
        await TaxiRepo.update(session, taxi_id, is_pinned=new_pin)

    action = "📌 Pinlandi!" if new_pin else "📌 Pindan olib tashlandi"
    await cb.answer(action, show_alert=True)
    logger.info("Admin taxi pin: id={} pinned={}", taxi_id, new_pin)


@router.callback_query(F.data.startswith("admin_taxi:delete:"))
async def admin_taxi_delete(cb: CallbackQuery) -> None:
    taxi_id = int(cb.data.split(":")[-1])
    async with get_session() as session:
        await TaxiRepo.delete(session, taxi_id)
    await cb.message.edit_text(f"🗑 Taxi #{taxi_id} o'chirildi.", reply_markup=None)
    await cb.answer("✅ O'chirildi")
    logger.info("Admin deleted taxi: {}", taxi_id)


@router.callback_query(F.data == "admin_taxi:add")
async def admin_taxi_add_start(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.taxi_add_driver)
    await cb.message.edit_text(
        "🚕 <b>Yangi taxi qo'shish</b>\n\n"
        "Haydovchining Telegram ID sini kiriting:\n"
        "<i>(Foydalanuvchi botda ro'yxatdan o'tgan bo'lishi kerak)</i>",
        parse_mode="HTML"
    )
    await cb.answer()


@router.message(AdminStates.taxi_add_driver)
async def admin_taxi_add_driver(message: Message, state: FSMContext) -> None:
    try:
        driver_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID! Raqam kiriting.")
        return

    async with get_session() as session:
        driver = await UserRepo.get(session, driver_id)

    if not driver:
        await message.answer(f"❌ ID {driver_id} bo'lgan foydalanuvchi topilmadi.")
        return

    await state.update_data(driver_id=driver_id)
    await state.set_state(AdminStates.taxi_add_countries)
    await message.answer(
        f"✅ Haydovchi: <b>{driver.full_name}</b>\n\n"
        f"🌍 Qaysi davlatlarga boradi? (vergul bilan):\n"
        f"<i>Misol: Latviya, Litva, Estoniya</i>",
        parse_mode="HTML"
    )


@router.message(AdminStates.taxi_add_countries)
async def admin_taxi_add_countries(message: Message, state: FSMContext) -> None:
    await state.update_data(countries=message.text)
    await state.set_state(AdminStates.taxi_add_cargo)
    await message.answer(
        "📦 Qanday yuklar qabul qiladi?\n"
        "<i>Misol: Kichik paketlar, Katta yuk, Faqat yo'lovchilar</i>",
        parse_mode="HTML"
    )


@router.message(AdminStates.taxi_add_cargo)
async def admin_taxi_add_cargo(message: Message, state: FSMContext) -> None:
    await state.update_data(cargo_types=message.text)
    await state.set_state(AdminStates.taxi_add_capacity)
    await message.answer("👥 Necha kishi/o'rin? (raqam):")


@router.message(AdminStates.taxi_add_capacity)
async def admin_taxi_add_capacity(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip().isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    await state.update_data(capacity=int(message.text.strip()))
    await state.set_state(AdminStates.taxi_add_desc)
    await message.answer(
        "📝 Qo'shimcha ma'lumot (narx, vaqt, bog'lanish usuli):\n"
        "<i>Yoki « - » yozing</i>",
        parse_mode="HTML"
    )


@router.message(AdminStates.taxi_add_desc)
async def admin_taxi_add_desc(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    description = message.text if message.text and message.text.strip() != "-" else None

    async with get_session() as session:
        taxi = await TaxiRepo.create(
            session,
            driver_id=data["driver_id"],
            countries=data["countries"],
            cargo_types=data["cargo_types"],
            passenger_capacity=data["capacity"],
            description=description,
            is_active=True,
        )
        taxi_id = taxi.id

    await state.clear()

    # Haydovchiga xabar
    try:
        await message.bot.send_message(
            data["driver_id"],
            "🚕 <b>E'loningiz qo'shildi!</b>\n\nSizning taxi xizmatingiz botda faollashtirildi. "
            "Foydalanuvchilar siz bilan bog'lanishi mumkin!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Taxi #{taxi_id} qo'shildi!</b>\n\n"
        f"🌍 Davlatlar: {data['countries']}\n"
        f"📦 Yuklar: {data['cargo_types']}\n"
        f"👥 Sig'im: {data['capacity']} kishi",
        parse_mode="HTML"
    )
    logger.info("Admin added taxi: id={} driver={}", taxi_id, data["driver_id"])


@router.callback_query(F.data.startswith("admin_taxi:approve_req:"))
async def admin_taxi_approve_request(cb: CallbackQuery, state: FSMContext) -> None:
    user_id = int(cb.data.split(":")[-1])
    # Admin to'g'ridan-to'g'ri qo'shish uchun state ga o'tadi
    await state.update_data(driver_id=user_id)
    await state.set_state(AdminStates.taxi_add_countries)

    async with get_session() as session:
        driver = await UserRepo.get(session, user_id)

    name = driver.full_name if driver else f"ID:{user_id}"
    await cb.message.edit_text(
        f"✅ Haydovchi: <b>{name}</b>\n\n"
        f"So'rov ma'lumotlari asosida davomini kiriting.\n\n"
        f"🌍 Davlatlar (vergul bilan):",
        parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_taxi:reject_req:"))
async def admin_taxi_reject_request(cb: CallbackQuery) -> None:
    user_id = int(cb.data.split(":")[-1])
    try:
        await cb.bot.send_message(
            user_id,
            "❌ <b>Taxi so'rovingiz rad etildi.</b>\n\n"
            "Qo'shimcha ma'lumot uchun admin bilan bog'laning.",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await cb.message.edit_text(f"❌ #{user_id} ning taxi so'rovi rad etildi.")
    await cb.answer("❌ Rad etildi")
