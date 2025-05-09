import uuid
from decimal import Decimal

from typing import Annotated
from datetime import datetime
from sqlalchemy import func, TIMESTAMP, Integer, inspect
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine, AsyncSession)

from app.config import database_url

engine = create_async_engine(url=database_url)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession,
                                         expire_on_commit=False)
int_uniq = Annotated[int,
                     mapped_column(primary_key=True, autoincrement=True)]
str_uniq = Annotated[str,
                     mapped_column(unique=True, nullable=False)]


class Base(AsyncAttrs, DeclarativeBase):
    # Sqlalchemy feature. This class won't be mapped to database
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP,
                                                 server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP,
                                                 server_default=func.now(),
                                                 onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})>"

    def to_dict(self, exclude_none: bool = False):
        """
        Transform object to dictionary

        Args:
            exclude_none (bool): whether exclude nones from result

        Returns:
            dict: dictionary with object's data
        """
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.key)

            # Case of special types
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, uuid.UUID):
                value = str(value)

            # Add to results with None filtering
            if not exclude_none or value is not None:
                result[column.key] = value

        return result
