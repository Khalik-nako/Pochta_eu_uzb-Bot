"""
Deal (kelishuv) modeli.
"""
import enum
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum,
    ForeignKey, Integer, SmallInteger, Text, func
)
from sqlalchemy.orm import relationship
from .base import Base


class DealStatus(str, enum.Enum):
    requested = "requested"       # So'rov yuborildi
    negotiating = "negotiating"   # Muzokaralar ketmoqda
    confirmed = "confirmed"       # Ikkalasi kelishdi
    delivered = "delivered"       # Yetkazildi (kutish)
    completed = "completed"       # Tugallandi
    disputed = "disputed"         # Shikoyat bor


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("courier_listings.id"), nullable=False)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    courier_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(DealStatus), default=DealStatus.requested)
    pickup_address = Column(Text, nullable=True)
    pickup_time = Column(DateTime(timezone=True), nullable=True)
    sender_confirmed = Column(Boolean, default=False)
    courier_confirmed = Column(Boolean, default=False)
    sender_rating = Column(SmallInteger, nullable=True)    # 1-5
    courier_rating = Column(SmallInteger, nullable=True)   # 1-5
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relations
    listing = relationship("CourierListing", back_populates="deals")
    sender = relationship("User", back_populates="sent_deals", foreign_keys=[sender_id])
    courier = relationship("User", back_populates="courier_deals", foreign_keys=[courier_id])
    messages = relationship("ChatMessage", back_populates="deal")
    complaints = relationship("Complaint", back_populates="deal")

    def __repr__(self) -> str:
        return f"<Deal id={self.id} status={self.status}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    sender_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    deal = relationship("Deal", back_populates="messages")
    sender_user = relationship("User", foreign_keys=[sender_id])
