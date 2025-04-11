from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.database import async_session_maker


async def get_session_with_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session with automatic commit

    Yields:
        session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session_no_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session without automatic commit

    Yields:
        session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
