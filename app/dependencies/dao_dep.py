from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.database import async_session_maker

async def get_session(auto_commit = True) -> AsyncGenerator[AsyncSession, None]:
    """Assync session

        Args:
            auto_commit (bool): whether perform commit after session end

        Yields:
            session
    """
    async with async_session_maker() as session:
        try:
            yield session

            if auto_commit:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
