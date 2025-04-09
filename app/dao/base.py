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

    def __init__(self, session: AsyncSession):
        self._session = session
        if self.model is None:
            raise ValueError("Model model must be defined in child class")

    async def find_one_or_none_by_id(self, data_id: int):
        """
        Finds a record by given id
        """
        try:
            query = select(self.model).filter_by(id=data_id)
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()

            log_message = f"Record {self.model.__name__} with ID {data_id} {'found' if record else 'not found'}."
            logger.info(log_message)

            return record
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding record with ID {data_id}: {e}")
            raise

    async def find_one_or_none(self, filters: BaseModel):
        """
        Finds a record by given filters
        """
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Searching a record {self.model.__name__} using filters: {filter_dict}")

        try:
            query = select(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()

            log_message = f"Record {'found' if record else 'not found'} using filters: {filter_dict}"
            logger.info(log_message)

            return record
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding record with filters {filter_dict}: {e}")
            raise

    async def find_all(self, filters: BaseModel | None = None):
        """
        Finds all records with optional filters
        """
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Searching all record {self.model.__name__} with filters: {filter_dict}")

        try:
            query = select(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            records = result.scalars().all()

            logger.info(f"Found {len(records)} records.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Internal error while finding all record with filters {filter_dict}: {e}")
            raise

    async def add(self, values: BaseModel):
        """
        Adds a new record with given values
        """
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Adding a record {self.model.__name__} with values: {values_dict}")
        try:
            new_instance = self.model(**values_dict)
            self._session.add(new_instance)
            await self._session.flush()

            logger.info(f"Record {self.model.__name__} is successfully added.")
            return new_instance
        except SQLAlchemyError as e:
            logger.error(f"Internal error while adding a record with values {values_dict}: {e}")
            raise

    async def add_many(self, instances: List[BaseModel]):
        """
        Adds multiple records with given values
        """
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(f"Adding {len(values_list)} records {self.model.__name__}. ")
        try:
            new_instances = [self.model(**values) for values in values_list]
            self._session.add_all(new_instances)
            await self._session.flush()

            logger.info(f"Successfully added {len(new_instances)} записей.")
            return new_instances
        except SQLAlchemyError as e:
            logger.error(f"Internal error while adding {len(values_list)} records: {e}")
            raise

    async def update(self, filters: BaseModel, values: BaseModel):
        """
        Updates records using filters with given values

        """
        filter_dict = filters.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        logger.info( 
            f"Updating records {self.model.__name__} with filters: {filter_dict} with values: {values_dict}")

        try:
            query = (
                sqlalchemy_update(self.model)
                .where(*[getattr(self.model, k) == v for k, v in filter_dict.items()])
                .values(**values_dict)
                .execution_options(synchronize_session="fetch")
            )
            result = await self._session.execute(query)
            await self._session.flush()

            logger.info(f"Updated {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Internal error while updating records: {e}")
            raise

    async def delete(self, filters: BaseModel):
        """
        Deletes records using filters
        """
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Deleting records {self.model.__name__} with filter: {filter_dict}")

        if not filter_dict:
            msg = "At least 1 filter must be provided for deleting"
            logger.error(msg)
            raise ValueError(msg)
        try:
            query = sqlalchemy_delete(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            await self._session.flush()

            logger.info(f"Deleted {result.rowcount} records.")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Internal error while deleting records: {e}")
            raise
