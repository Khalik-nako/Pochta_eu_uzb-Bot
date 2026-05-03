"""
Kuryer e'loni modeli.
"""
import enum
import json
from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Enum,
    Float, ForeignKey, Integer, String, Text, func, TypeDecorator
)
from sqlalchemy.orm import relationship
from .base import Base


class JSONList(TypeDecorator):
    """JSON formatda ro'yxat saqlash (SQLite va PostgreSQL mos)."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []


class ListingStatus(str, enum.Enum):
    pending = "pending"       # Admin tasdiqlashini kutmoqda
    active = "active"         # Faol e'lon
    completed = "completed"   # Tugallangan
    deleted = "deleted"       # O'chirilgan


class CourierListing(Base):
    __tablename__ = "courier_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    from_country = Column(String(100), nullable=False)
    from_city = Column(String(100), nullable=False)
    flight_date = Column(Date, nullable=False)
    flight_time = Column(String(5), nullable=False)   # "HH:MM" format
    max_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    restrictions = Column(JSONList, default=[])  # ["Dori", "Suyuqlik"]
    custom_restriction = Column(Text, nullable=True)
    video_msg_id = Column(String(50), nullable=True)  # TG kanal message ID
    status = Column(Enum(ListingStatus), default=ListingStatus.pending)
    is_verified = Column(Boolean, default=False)
    age_verified = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    has_diamond = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Reys sanasidan keyin auto-o'chadi

    # Relations
    user = relationship("User", back_populates="courier_listings", foreign_keys=[user_id])
    deals = relationship("Deal", back_populates="listing")

    def __repr__(self) -> str:
        return f"<CourierListing id={self.id} {self.from_city}→Toshkent {self.flight_date}>"
