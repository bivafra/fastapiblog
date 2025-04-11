from types import ClassMethodDescriptorType
from typing import List, TypeVar, Generic, Type
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Base

T = TypeVar("T", bound=Base)

class BaseDAO(Generic[T]):
    model: Type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, session: AsyncSession, data_id: int):
        """
        Finds a record by given id
        """
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()

            log_message = f"Record {cls.model.__name__} with ID {data_id} {'found' if record else 'not found'}."
            logger.info(log_message)

            return record
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding record with ID {data_id}: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        """
        Finds a record by given filters
        """
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Searching a record {cls.model.__name__} using filters: {filter_dict}")

        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()

            log_message = f"Record {'found' if record else 'not found'} using filters: {filter_dict}"
            logger.info(log_message)

            return record
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding record with filters {filter_dict}: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None):
        """
        Finds all records with optional filters
        """
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Searching all record {cls.model.__name__} with filters: {filter_dict}")

        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()

            logger.info(f"Found {len(records)} records.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding all record with filters {filter_dict}: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        """
        Adds a new record with given values
        """
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Adding a record {cls.model.__name__} with values: {values_dict}")
        try:
            new_instance = cls.model(**values_dict)
            session.add(new_instance)
            await session.flush()

            logger.info(f"Record {cls.model.__name__} is successfully added.")
            return new_instance
        except SQLAlchemyError as e:
            logger.error(f"Internal error while adding a record with values {values_dict}: {e}")
            raise

    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[BaseModel]):
        """
        Adds multiple records with given values
        """
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(f"Adding {len(values_list)} records {cls.model.__name__}. ")
        try:
            new_instances = [cls.model(**values) for values in values_list]
            session.add_all(new_instances)
            await session.flush()

            logger.info(f"Successfully added {len(new_instances)} записей.")
            return new_instances
        except SQLAlchemyError as e:
            logger.error(f"Internal error while adding {len(values_list)} records: {e}")
            raise

    @classmethod
    async def update(cls, session: AsyncSession, filters: BaseModel, values: BaseModel):
        """
        Updates records using filters with given values

        """
        filter_dict = filters.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        logger.info( 
            f"Updating records {cls.model.__name__} with filters: {filter_dict} with values: {values_dict}")

        try:
            query = (
                sqlalchemy_update(cls.model)
                .where(*[getattr(cls.model, k) == v for k, v in filter_dict.items()])
                .values(**values_dict)
                .execution_options(synchronize_session="fetch")
            )
            result = await session.execute(query)
            await session.flush()

            logger.info(f"Updated {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Internal error while updating records: {e}")
            raise

    @classmethod
    async def delete(cls, session: AsyncSession, filters: BaseModel):
        """
        Deletes records using filters
        """
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Deleting records {cls.model.__name__} with filter: {filter_dict}")

        if not filter_dict:
            msg = "At least 1 filter must be provided for deleting"
            logger.error(msg)
            raise ValueError(msg)
        try:
            query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            await session.flush()

            logger.info(f"Deleted {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Internal error while deleting records: {e}")
            raise
