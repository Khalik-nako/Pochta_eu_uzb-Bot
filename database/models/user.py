"""
Foydalanuvchi modeli.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float,
    Integer, String, func
)
from sqlalchemy.orm import relationship
from .base import Base
import enum


class BlockType(str, enum.Enum):
    temp = "temp"
    permanent = "permanent"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)           # Telegram user ID
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    language = Column(String(2), nullable=False, default="uz")  # 'uz' yoki 'ru'
    country = Column(String(100))
    timezone = Column(String(50), default="Europe/Riga")
    city = Column(String(100))
    lat = Column(Float)
    lon = Column(Float)
    is_blocked = Column(Boolean, default=False)
    block_type = Column(Enum(BlockType), nullable=True)
    rating = Column(Float, default=0.0)
    deal_count = Column(Integer, default=0)
    legal_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    courier_listings = relationship("CourierListing", back_populates="user", foreign_keys="CourierListing.user_id")
    sent_deals = relationship("Deal", back_populates="sender", foreign_keys="Deal.sender_id")
    courier_deals = relationship("Deal", back_populates="courier", foreign_keys="Deal.courier_id")
    complaints_sent = relationship("Complaint", back_populates="from_user", foreign_keys="Complaint.from_id")
    subscriptions = relationship("CourierSubscription", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.full_name} lang={self.language}>"
