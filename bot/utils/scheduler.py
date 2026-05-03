"""
APScheduler — avtomatik vazifalar.
• Har kuni ertalab: ertaga reysga ketadiganlarni tekshirish (S-33)
• Har soatda: o'tib ketgan e'lonlarni o'chirish
"""
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from loguru import logger

try:
    import pytz
    _scheduler_tz = pytz.utc
except ImportError:
    _scheduler_tz = "UTC"

from config import config
from database import get_session, DealRepo, ListingRepo
from database.models import DealStatus, ListingStatus
from bot.utils.notifications import notify_username_share, notify_delivery_check


scheduler = AsyncIOScheduler(timezone=_scheduler_tz)


def setup_scheduler(bot: Bot) -> None:
    """Scheduler'ni sozlash va ishga tushirish."""

    @scheduler.scheduled_job("cron", hour=8, minute=0, id="username_share")
    async def share_usernames_tomorrow_flights():
        """
        Har kuni soat 08:00 UTC da: ertaga reysga ketadiganlarni topib,
        ikki tomonga username yuborish (eslatma sifatida).
        """
        logger.info("⏰ Username almashish eslatmasi boshlandi")
        try:
            async with get_session() as session:
                deals = await DealRepo.get_confirmed_tomorrow(session)
                logger.info("✈️ Ertaga reys: {} ta deal", len(deals))
                for deal in deals:
                    try:
                        courier_chat = await bot.get_chat(deal.courier_id)
                        courier_username = f"@{courier_chat.username}" if courier_chat.username else f"ID: {deal.courier_id}"
                    except Exception:
                        courier_username = f"ID: {deal.courier_id}"

                    try:
                        sender_chat = await bot.get_chat(deal.sender_id)
                        sender_username = f"@{sender_chat.username}" if sender_chat.username else f"ID: {deal.sender_id}"
                    except Exception:
                        sender_username = f"ID: {deal.sender_id}"

                    await notify_username_share(
                        bot, deal.sender_id, deal.sender.language,
                        courier_username, is_sender=True,
                    )
                    await notify_username_share(
                        bot, deal.courier_id, deal.courier.language,
                        sender_username, is_sender=False,
                    )
        except Exception as e:
            logger.error("❌ Username share scheduler xatosi: {}", e)

    @scheduler.scheduled_job("cron", hour=20, minute=0, id="delivery_check")
    async def check_delivery_after_flight():
        """
        Har kuni soat 20:00 UTC: bugun reysga ketgan deallarni topib,
        ikki tomonga yetkazilish tekshiruvi yuborish.
        """
        logger.info("📦 Reys tugagandan keyin delivery check boshlandi")
        try:
            from datetime import date
            from sqlalchemy import and_, select
            from database.models import CourierListing, Deal, DealStatus
            today = date.today()

            async with get_session() as session:
                from sqlalchemy.orm import joinedload
                result = await session.execute(
                    select(Deal)
                    .options(
                        joinedload(Deal.sender),
                        joinedload(Deal.courier),
                        joinedload(Deal.listing),
                    )
                    .join(CourierListing, Deal.listing_id == CourierListing.id)
                    .where(
                        and_(
                            Deal.status == DealStatus.confirmed,
                            CourierListing.flight_date == today,
                        )
                    )
                )
                today_deals = list(result.scalars().all())
                logger.info("🛬 Bugun reys bo'lgan deallar: {} ta", len(today_deals))

                for deal in today_deals:
                    await notify_delivery_check(
                        bot,
                        courier_id=deal.courier_id,
                        courier_lang=deal.courier.language if deal.courier else "uz",
                        sender_id=deal.sender_id,
                        sender_lang=deal.sender.language if deal.sender else "uz",
                        deal_id=deal.id,
                    )
        except Exception as e:
            logger.error("❌ Delivery check scheduler xatosi: {}", e)

    @scheduler.scheduled_job("cron", hour="*/2", id="expire_listings")
    async def expire_old_listings():
        """Har 2 soatda: reysdan o'tib ketgan e'lonlarni o'chirish."""
        logger.info("🗑️ Eskirgan e'lonlarni tekshirish...")
        try:
            async with get_session() as session:
                from sqlalchemy import update, and_
                from datetime import date
                from database.models import CourierListing
                today = date.today()
                # O'tib ketgan faol e'lonlarni o'chirish
                await session.execute(
                    update(CourierListing)
                    .where(
                        and_(
                            CourierListing.status == ListingStatus.active,
                            CourierListing.flight_date < today,
                        )
                    )
                    .values(status=ListingStatus.deleted)
                )
                logger.info("✅ Eskirgan e'lonlar o'chirildi")
        except Exception as e:
            logger.error("❌ Expire listings scheduler xatosi: {}", e)

    scheduler.start()
    logger.info("⏰ Scheduler ishga tushdi")
