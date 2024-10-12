from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings.base import config_env

if config_env.database_url is None:
    raise ValueError("Database URL must be set in the configuration.")

engine = create_async_engine(config_env.database_url.replace("postgresql://", "postgresql+asyncpg://"), echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
