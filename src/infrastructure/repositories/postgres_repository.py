from typing import Optional, TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.domain.interfaces.repository import Repository
from src.infrastructure.config.database import get_session, init_db, async_session
from src.config.config import load_config
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')

class PostgresRepository(Repository[T]):
    def __init__(self, entity_type: Type[T]):
        self._entity_type = entity_type
        self._db: Optional[AsyncSession] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        if not self._initialized:
            if not async_session:
                config = load_config()
                await init_db(config.database)
            self._initialized = True
    
    @asynccontextmanager
    async def _get_session(self):
        """Récupère une session de base de données dans un contexte"""
        await self._ensure_initialized()
        if async_session:
            async with async_session() as session:
                try:
                    yield session
                finally:
                    await session.close()
        else:
            raise RuntimeError("La session de base de données n'est pas initialisée")

    async def get(self, id: int) -> Optional[T]:
        async with self._get_session() as session:
            query = select(self._entity_type).filter_by(id=id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def save(self, entity: T) -> T:
        async with self._get_session() as session:
            try:
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
                return entity
            except SQLAlchemyError as e:
                await session.rollback()
                raise

    async def update(self, entity: T) -> T:
        async with self._get_session() as session:
            try:
                query = select(self._entity_type).filter_by(id=entity.id)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    raise ValueError(f"L'entité avec l'ID {entity.id} n'existe pas")
                
                await session.commit()
                await session.refresh(entity)
                return entity
            except SQLAlchemyError as e:
                await session.rollback()
                raise

    async def delete(self, id: int) -> None:
        async with self._get_session() as session:
            try:
                query = select(self._entity_type).filter_by(id=id)
                result = await session.execute(query)
                entity = result.scalar_one_or_none()
                
                if not entity:
                    raise ValueError(f"L'entité avec l'ID {id} n'existe pas")
                
                await session.delete(entity)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise 