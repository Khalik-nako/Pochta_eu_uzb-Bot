"""
Shikoyat va Blacklist modellari.
"""
import enum
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum,
    ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import relationship
from .base import Base


class ComplaintStatus(str, enum.Enum):
    new = "new"
    reviewing = "reviewing"
    resolved = "resolved"
    closed = "closed"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=True)
    from_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    against_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.new)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    deal = relationship("Deal", back_populates="complaints")
    from_user = relationship("User", back_populates="complaints_sent", foreign_keys=[from_id])
    against_user = relationship("User", foreign_keys=[against_id])


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=True)
    telegram_id = Column(BigInteger, nullable=True)
    reason = Column(Text, nullable=True)
    banned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_permanent = Column(Boolean, default=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CourierSubscription(Base):
    """Kuryer topilmasa, xabar so'ragan foydalanuvchilar."""
    __tablename__ = "courier_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    country = Column(String(100), nullable=False)
    month = Column(String(7), nullable=False)  # '2026-05'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")


class TaxiService(Base):
    """Yevropa bo'ylab taxi xizmatlari."""
    __tablename__ = "taxi_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    countries = Column(String(500), nullable=False)       # "Latviya,Litva,Estoniya"
    cargo_types = Column(String(500), nullable=False)     # "Kichik yuk,Katta yuk,Odamlar"
    passenger_capacity = Column(Integer, nullable=False, default=4)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    has_diamond = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    driver = relationship("User", foreign_keys=[driver_id])
