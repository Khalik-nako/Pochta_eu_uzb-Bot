"""
Repository — barcha DB operatsiyalar shu yerda.
Service va handler'lar to'g'ridan-to'g'ri DB ga tegmaydi.
"""
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, func, or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from .models import (
    User, BlockType,
    CourierListing, ListingStatus,
    Deal, DealStatus, ChatMessage,
    Complaint, ComplaintStatus,
    Blacklist, Notification, CourierSubscription,
    TaxiService,
)


# ─────────────────────────────────────────────
#  USER REPOSITORY
# ─────────────────────────────────────────────

class UserRepo:

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> Optional[User]:
        return await session.get(User, user_id)

    @staticmethod
    async def get_by_phone(session: AsyncSession, phone: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> User:
        user = User(**kwargs)
        session.add(user)
        await session.flush()
        logger.info("👤 Yangi foydalanuvchi: id={} name={}", user.id, user.full_name)
        return user

    @staticmethod
    async def update(session: AsyncSession, user_id: int, **kwargs) -> None:
        await session.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )

    @staticmethod
    async def is_blacklisted(session: AsyncSession, phone: str, telegram_id: int) -> bool:
        result = await session.execute(
            select(Blacklist).where(
                or_(Blacklist.phone == phone, Blacklist.telegram_id == telegram_id)
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_all(session: AsyncSession) -> List[User]:
        result = await session.execute(select(User).where(User.is_blocked == False))
        return list(result.scalars().all())

    @staticmethod
    async def count_new_today(session: AsyncSession) -> int:
        today = datetime.now(timezone.utc).date()
        result = await session.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        return result.scalar() or 0


# ─────────────────────────────────────────────
#  COURIER LISTING REPOSITORY
# ─────────────────────────────────────────────

class ListingRepo:

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> CourierListing:
        listing = CourierListing(**kwargs)
        session.add(listing)
        await session.flush()
        logger.info("✈️ Yangi e'lon: id={} user_id={}", listing.id, listing.user_id)
        return listing

    @staticmethod
    async def get(session: AsyncSession, listing_id: int) -> Optional[CourierListing]:
        """Listing + user eager load (MissingGreenlet bug fixu)."""
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(CourierListing)
            .options(selectinload(CourierListing.user))
            .where(CourierListing.id == listing_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_by_month(
        session: AsyncSession,
        country: str,
        year: int,
        month: int,
        sort_by: str = "date",   # "date" | "price" | "rating"
    ) -> List[CourierListing]:
        """Faol e'lonlarni oy bo'yicha filtrlash."""
        from sqlalchemy.orm import joinedload

        q = (
            select(CourierListing)
            .options(joinedload(CourierListing.user))
            .where(
                and_(
                    CourierListing.from_country == country,
                    CourierListing.status == ListingStatus.active,
                    func.extract("year", CourierListing.flight_date) == year,
                    func.extract("month", CourierListing.flight_date) == month,
                )
            )
        )
        if sort_by == "price":
            q = q.order_by(CourierListing.price_per_kg.asc())
        elif sort_by == "rating":
            from .models import User as U
            q = q.join(User, User.id == CourierListing.user_id).order_by(User.rating.desc())
        else:
            q = q.order_by(CourierListing.flight_date.asc())

        result = await session.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int) -> List[CourierListing]:
        result = await session.execute(
            select(CourierListing)
            .where(CourierListing.user_id == user_id)
            .order_by(CourierListing.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession, listing_id: int, status: ListingStatus
    ) -> None:
        await session.execute(
            update(CourierListing)
            .where(CourierListing.id == listing_id)
            .values(status=status)
        )

    @staticmethod
    async def get_pending(session: AsyncSession) -> List[CourierListing]:
        """Admin tasdiqlashini kutayotgan e'lonlar."""
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(CourierListing)
            .options(joinedload(CourierListing.user))
            .where(CourierListing.status == ListingStatus.pending)
            .order_by(CourierListing.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_active(session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count(CourierListing.id)).where(
                CourierListing.status == ListingStatus.active
            )
        )
        return result.scalar() or 0


# ─────────────────────────────────────────────
#  DEAL REPOSITORY
# ─────────────────────────────────────────────

class DealRepo:

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> Deal:
        deal = Deal(**kwargs)
        session.add(deal)
        await session.flush()
        logger.info("🤝 Yangi deal: id={}", deal.id)
        return deal

    @staticmethod
    async def get(session: AsyncSession, deal_id: int) -> Optional[Deal]:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Deal)
            .options(
                joinedload(Deal.sender),
                joinedload(Deal.courier),
                joinedload(Deal.listing),
            )
            .where(Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int) -> List[Deal]:
        result = await session.execute(
            select(Deal)
            .where(or_(Deal.sender_id == user_id, Deal.courier_id == user_id))
            .order_by(Deal.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(session: AsyncSession, deal_id: int, status: DealStatus) -> None:
        await session.execute(
            update(Deal).where(Deal.id == deal_id).values(status=status)
        )

    @staticmethod
    async def confirm_delivery(
        session: AsyncSession, deal_id: int, is_sender: bool
    ) -> Deal:
        field = "sender_confirmed" if is_sender else "courier_confirmed"
        await session.execute(
            update(Deal).where(Deal.id == deal_id).values(**{field: True})
        )
        return await DealRepo.get(session, deal_id)

    @staticmethod
    async def set_rating(
        session: AsyncSession, deal_id: int, is_sender: bool, rating: int
    ) -> None:
        field = "sender_rating" if is_sender else "courier_rating"
        await session.execute(
            update(Deal).where(Deal.id == deal_id).values(**{field: rating})
        )

    @staticmethod
    async def count_completed_today(session: AsyncSession) -> int:
        today = datetime.now(timezone.utc).date()
        result = await session.execute(
            select(func.count(Deal.id)).where(
                and_(
                    Deal.status == DealStatus.completed,
                    func.date(Deal.completed_at) == today,
                )
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def get_confirmed_tomorrow(session: AsyncSession) -> List[Deal]:
        """Ertaga reysga ketadigan tasdiqlanган deallar (username almashish uchun)."""
        from datetime import timedelta
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Deal)
            .options(joinedload(Deal.listing), joinedload(Deal.sender), joinedload(Deal.courier))
            .join(CourierListing, Deal.listing_id == CourierListing.id)
            .where(
                and_(
                    Deal.status == DealStatus.confirmed,
                    CourierListing.flight_date == tomorrow,
                )
            )
        )
        return list(result.scalars().all())


# ─────────────────────────────────────────────
#  CHAT MESSAGE REPOSITORY
# ─────────────────────────────────────────────

class ChatRepo:

    @staticmethod
    async def add_message(
        session: AsyncSession, deal_id: int, sender_id: int, text: str
    ) -> ChatMessage:
        msg = ChatMessage(deal_id=deal_id, sender_id=sender_id, text=text)
        session.add(msg)
        await session.flush()
        return msg

    @staticmethod
    async def get_messages(session: AsyncSession, deal_id: int) -> List[ChatMessage]:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.deal_id == deal_id)
            .order_by(ChatMessage.sent_at.asc())
        )
        return list(result.scalars().all())


# ─────────────────────────────────────────────
#  COMPLAINT REPOSITORY
# ─────────────────────────────────────────────

class ComplaintRepo:

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> Complaint:
        complaint = Complaint(**kwargs)
        session.add(complaint)
        await session.flush()
        logger.warning("🚨 Yangi shikoyat: from_id={} against_id={}", complaint.from_id, complaint.against_id)
        return complaint

    @staticmethod
    async def get_new(session: AsyncSession) -> List[Complaint]:
        from sqlalchemy.orm import joinedload
        result = await session.execute(
            select(Complaint)
            .options(joinedload(Complaint.from_user), joinedload(Complaint.against_user))
            .where(Complaint.status == ComplaintStatus.new)
            .order_by(Complaint.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(session: AsyncSession, complaint_id: int, status: ComplaintStatus) -> None:
        await session.execute(
            update(Complaint).where(Complaint.id == complaint_id).values(status=status)
        )

    @staticmethod
    async def count_new(session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count(Complaint.id)).where(Complaint.status == ComplaintStatus.new)
        )
        return result.scalar() or 0


# ─────────────────────────────────────────────
#  BLACKLIST REPOSITORY
# ─────────────────────────────────────────────

class BlacklistRepo:

    @staticmethod
    async def add(session: AsyncSession, **kwargs) -> Blacklist:
        entry = Blacklist(**kwargs)
        session.add(entry)
        await session.flush()
        logger.warning("🚫 Blacklistga qo'shildi: phone={} tg_id={}", kwargs.get("phone"), kwargs.get("telegram_id"))
        return entry

    @staticmethod
    async def is_blocked(session: AsyncSession, phone: str, telegram_id: int) -> bool:
        result = await session.execute(
            select(Blacklist).where(
                or_(Blacklist.phone == phone, Blacklist.telegram_id == telegram_id)
            )
        )
        return result.scalar_one_or_none() is not None


# ─────────────────────────────────────────────
#  SUBSCRIPTION REPOSITORY
# ─────────────────────────────────────────────

class SubscriptionRepo:

    @staticmethod
    async def add(session: AsyncSession, user_id: int, country: str, month: str) -> None:
        # Avval mavjudligini tekshirish
        result = await session.execute(
            select(CourierSubscription).where(
                and_(
                    CourierSubscription.user_id == user_id,
                    CourierSubscription.country == country,
                    CourierSubscription.month == month,
                )
            )
        )
        if not result.scalar_one_or_none():
            session.add(CourierSubscription(user_id=user_id, country=country, month=month))

    @staticmethod
    async def get_subscribers(session: AsyncSession, country: str, month: str) -> List[CourierSubscription]:
        result = await session.execute(
            select(CourierSubscription).where(
                and_(
                    CourierSubscription.country == country,
                    CourierSubscription.month == month,
                )
            )
        )
        return list(result.scalars().all())


# ─────────────────────────────────────────────
#  TAXI SERVICE REPOSITORY
# ─────────────────────────────────────────────

class TaxiRepo:

    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> TaxiService:
        taxi = TaxiService(**kwargs)
        session.add(taxi)
        await session.flush()
        logger.info("🚕 Yangi taxi xizmati: id={} driver_id={}", taxi.id, taxi.driver_id)
        return taxi

    @staticmethod
    async def get(session: AsyncSession, taxi_id: int) -> Optional[TaxiService]:
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(TaxiService)
            .options(selectinload(TaxiService.driver))
            .where(TaxiService.id == taxi_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_active(session: AsyncSession) -> List[TaxiService]:
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(TaxiService)
            .options(selectinload(TaxiService.driver))
            .where(TaxiService.is_active == True)
            .order_by(TaxiService.is_pinned.desc(), TaxiService.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_driver(session: AsyncSession, driver_id: int) -> List[TaxiService]:
        result = await session.execute(
            select(TaxiService).where(TaxiService.driver_id == driver_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(session: AsyncSession, taxi_id: int, **kwargs) -> None:
        await session.execute(
            update(TaxiService).where(TaxiService.id == taxi_id).values(**kwargs)
        )

    @staticmethod
    async def delete(session: AsyncSession, taxi_id: int) -> None:
        await session.execute(
            update(TaxiService).where(TaxiService.id == taxi_id).values(is_active=False)
        )

    @staticmethod
    async def count_active(session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count(TaxiService.id)).where(TaxiService.is_active == True)
        )
        return result.scalar() or 0


# ─────────────────────────────────────────────
#  EXTENDED USER REPO — COUNTRY STATS
# ─────────────────────────────────────────────

class UserStatsRepo:

    @staticmethod
    async def count_by_country(session: AsyncSession) -> dict:
        """Har bir davlatdan qancha user borligini qaytaradi."""
        result = await session.execute(
            select(User.country, func.count(User.id))
            .where(User.is_blocked == False, User.country != None)
            .group_by(User.country)
            .order_by(func.count(User.id).desc())
        )
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def get_by_country(session: AsyncSession, country: str) -> List[User]:
        """Muayyan davlatdagi barcha foydalanuvchilar."""
        result = await session.execute(
            select(User).where(
                and_(User.country == country, User.is_blocked == False)
            )
        )
        return list(result.scalars().all())
