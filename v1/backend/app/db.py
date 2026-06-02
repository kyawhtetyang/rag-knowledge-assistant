from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import SETTINGS


ENGINE: AsyncEngine = create_async_engine(
    SETTINGS.database_url,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
