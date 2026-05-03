"""
Bildirishnomalar — barcha avtomatik xabarlar shu yerda.
Hech qachon to'g'ridan-to'g'ri bot.send_message ishlatmang!
"""
from aiogram import Bot
from loguru import logger

from locales import t


async def notify_courier_new_request(
    bot: Bot,
    courier_id: int,
    courier_lang: str,
    deal_id: int,
    sender_name: str,
    location: str,
    note: str = "—",
) -> None:
    """S-30: Kuryerga yangi so'rov haqida xabar."""
    from bot.keyboards.inline import deal_request_keyboard
    try:
        text = t(courier_lang, "NEW_REQUEST_FOR_COURIER",
                 sender_name=sender_name, location=location, note=note)
        await bot.send_message(
            courier_id,
            text,
            parse_mode="HTML",
            reply_markup=deal_request_keyboard(courier_lang, deal_id),
        )
        logger.info("📬 Kuryer {}ga yangi so'rov xabari yuborildi", courier_id)
    except Exception as e:
        logger.error("❌ Kuryer {}ga xabar yuborishda xato: {}", courier_id, e)


async def notify_sender_request_accepted(
    bot: Bot,
    sender_id: int,
    sender_lang: str,
) -> None:
    """Jo'natuvchiga: so'rov qabul qilindi."""
    try:
        text = t(sender_lang, "REQUEST_ACCEPTED")
        await bot.send_message(sender_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("❌ Jo'natuvchi {}ga xabar yuborishda xato: {}", sender_id, e)


async def notify_sender_request_rejected(
    bot: Bot,
    sender_id: int,
    sender_lang: str,
) -> None:
    """Jo'natuvchiga: so'rov rad etildi."""
    try:
        text = t(sender_lang, "REQUEST_REJECTED")
        await bot.send_message(sender_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("❌ Jo'natuvchi {}ga xabar yuborishda xato: {}", sender_id, e)


async def notify_deal_confirmed(
    bot: Bot,
    user_id: int,
    lang: str,
    city: str,
    date: str,
    time: str,
) -> None:
    """S-32: Deal tasdiqlandi xabari."""
    try:
        text = t(lang, "DEAL_CONFIRMED", city=city, date=date, time=time)
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("❌ Deal confirmed xabar xatosi {}: {}", user_id, e)


async def notify_username_share(
    bot: Bot,
    user_id: int,
    lang: str,
    username: str,
    is_sender: bool,
) -> None:
    """S-33: Username almashish."""
    try:
        key = "USERNAME_SHARE_SENDER" if is_sender else "USERNAME_SHARE_COURIER"
        text = t(lang, key, username=username)
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("❌ Username share xabar xatosi {}: {}", user_id, e)


async def notify_listing_approved(
    bot: Bot,
    user_id: int,
    lang: str,
    city: str,
    date: str,
    time: str,
    max_kg: float,
    price: float,
) -> None:
    """Admin tasdiqlaganda kuryer ga xabar."""
    try:
        text = t(lang, "LISTING_PUBLISHED",
                 city=city, date=date, time=time, max_kg=max_kg, price=price)
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error("❌ Listing approved xabar xatosi {}: {}", user_id, e)


async def notify_listing_rejected(
    bot: Bot,
    user_id: int,
    lang: str,
    reason: str,
) -> None:
    """Admin rad etganda kuryer ga xabar."""
    from bot.keyboards.inline import back_to_menu_keyboard
    try:
        text = t(lang, "VIDEO_REJECTED", reason=reason)
        await bot.send_message(
            user_id, text, parse_mode="HTML",
            reply_markup=back_to_menu_keyboard(lang),
        )
    except Exception as e:
        logger.error("❌ Listing rejected xabar xatosi {}: {}", user_id, e)


async def notify_admins(
    bot: Bot,
    admin_ids: list,
    text: str,
) -> None:
    """Barcha adminlarga xabar yuborish."""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error("❌ Admin {}ga xabar xatosi: {}", admin_id, e)


async def notify_subscription_match(
    bot: Bot,
    user_id: int,
    lang: str,
) -> None:
    """Obunachi uchun: yangi kuryer topildi."""
    try:
        text = (
            "🔔 Sizga mos kuryer topildi!" if lang == "uz"
            else "🔔 Найден подходящий для вас курьер!"
        )
        await bot.send_message(user_id, text)
    except Exception as e:
        logger.error("❌ Subscription notify xatosi {}: {}", user_id, e)


async def notify_delivery_check(
    bot,
    courier_id: int,
    courier_lang: str,
    sender_id: int,
    sender_lang: str,
    deal_id: int,
) -> None:
    """Reys tugaganidan keyin ikkala tomonga yetkazilish tekshiruvi."""
    from bot.keyboards.inline import delivery_confirm_keyboard

    # Kuryerga: yukni topshirdingizmi?
    courier_text = (
        "📦 <b>Reys yakunlandi!</b>\n\n"
        "Siz pochta jo'natuvchisiga yukni topshirdingizmi? "
        "Iltimos, tasdiqlang — bu deal uchun muhim!\n\n"
        "⚠️ Tasdiqlash ikkinchi tomon bilan bog'liq."
        if courier_lang == "uz" else
        "📦 <b>Рейс завершён!</b>\n\n"
        "Вы передали груз отправителю? "
        "Пожалуйста, подтвердите — это важно для сделки!\n\n"
        "⚠️ Подтверждение связано со второй стороной."
    )
    try:
        await bot.send_message(
            courier_id, courier_text,
            parse_mode="HTML",
            reply_markup=delivery_confirm_keyboard(courier_lang, deal_id, "courier"),
        )
    except Exception as e:
        logger.error("❌ Kuryer {}ga delivery check yuborishda xato: {}", courier_id, e)

    # Jo'natuvchiga: yukni oldingizmi?
    sender_text = (
        "📬 <b>Reys yakunlandi!</b>\n\n"
        "Kuryer sizga yukni yetkazib berdimi? "
        "Iltimos, qabul qilganingizni tasdiqlang!\n\n"
        "⚠️ Ikkalangiz tasdiqlasangiz deal yakunlanadi."
        if sender_lang == "uz" else
        "📬 <b>Рейс завершён!</b>\n\n"
        "Курьер доставил вам груз? "
        "Пожалуйста, подтвердите получение!\n\n"
        "⚠️ После подтверждения обеих сторон сделка завершится."
    )
    try:
        await bot.send_message(
            sender_id, sender_text,
            parse_mode="HTML",
            reply_markup=delivery_confirm_keyboard(sender_lang, deal_id, "sender"),
        )
    except Exception as e:
        logger.error("❌ Jo'natuvchi {}ga delivery check yuborishda xato: {}", sender_id, e)


async def notify_username_share_immediate(
    bot,
    deal,
) -> None:
    """
    Deal tasdiqlangandan so'ng darhol username almashish.
    (Eski scheduler: 1 kun qolganida. Bu: darhol + 1 kun qolganida ham yuboriladi.)
    """
    try:
        sender = deal.sender
        courier = deal.courier
        if not sender or not courier:
            return

        # Kuryer username'ini aniqlash
        courier_username_raw = courier.full_name  # fallback
        # Telegram username'ni olish uchun chat ID ishlatamiz
        try:
            courier_chat = await bot.get_chat(courier.id)
            courier_username = f"@{courier_chat.username}" if courier_chat.username else f"ID: {courier.id}"
        except Exception:
            courier_username = f"ID: {courier.id}"

        try:
            sender_chat = await bot.get_chat(sender.id)
            sender_username = f"@{sender_chat.username}" if sender_chat.username else f"ID: {sender.id}"
        except Exception:
            sender_username = f"ID: {sender.id}"

        # Jo'natuvchiga kuryer kontakti
        sender_msg = (
            f"✅ <b>Deal tasdiqlandi!</b>\n\n"
            f"Kuryer ma'lumotlari:\n"
            f"👤 Ism: {courier.full_name}\n"
            f"📱 Telegram: {courier_username}\n"
            f"📞 Telefon: {courier.phone}\n\n"
            f"Reys sanasi va vaqt haqida kuryer bilan to'g'ridan-to'g'ri gaplashing."
            if sender.language == "uz" else
            f"✅ <b>Сделка подтверждена!</b>\n\n"
            f"Данные курьера:\n"
            f"👤 Имя: {courier.full_name}\n"
            f"📱 Telegram: {courier_username}\n"
            f"📞 Телефон: {courier.phone}\n\n"
            f"Свяжитесь с курьером напрямую по дате и времени."
        )
        await bot.send_message(sender.id, sender_msg, parse_mode="HTML")

        # Kuryerga jo'natuvchi kontakti
        courier_msg = (
            f"✅ <b>Deal tasdiqlandi!</b>\n\n"
            f"Jo'natuvchi ma'lumotlari:\n"
            f"👤 Ism: {sender.full_name}\n"
            f"📱 Telegram: {sender_username}\n"
            f"📞 Telefon: {sender.phone}\n\n"
            f"Jo'natuvchi bilan to'g'ridan-to'g'ri aloqaga chiqing."
            if courier.language == "uz" else
            f"✅ <b>Сделка подтверждена!</b>\n\n"
            f"Данные отправителя:\n"
            f"👤 Имя: {sender.full_name}\n"
            f"📱 Telegram: {sender_username}\n"
            f"📞 Телефон: {sender.phone}\n\n"
            f"Свяжитесь с отправителем напрямую."
        )
        await bot.send_message(courier.id, courier_msg, parse_mode="HTML")

        logger.info("✅ Darhol username almashish: deal_id={}", deal.id)
    except Exception as e:
        logger.error("❌ Darhol username share xatosi: {}", e)
