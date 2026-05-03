"""
Asinxron DB ulanishi — SQLAlchemy (SQLite yoki PostgreSQL).
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from config import config
from .models.base import Base


# SQLite uchun pool parametrlari ishlatilmaydi
_is_sqlite = config.db.url.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(
        config.db.url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        config.db.url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# Session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    """Barcha jadvallarni yaratish (birinchi ishga tushirishda)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Jadvallar yaratildi yoki mavjud")


async def drop_tables() -> None:
    """Barcha jadvallarni o'chirish (faqat dev uchun!)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("⚠️ Barcha jadvallar o'chirildi!")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager — session olish va avtomatik yopish."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
