from typing import Optional, TypeVar, Generic, Type, Protocol
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.domain.interfaces.repository import Repository
from src.infrastructure.config.database import get_session, init_db, async_session
from src.config.config import load_config
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class HasId(Protocol):
    """Protocole définissant une entité avec un identifiant.
    
    Ce protocole est utilisé pour garantir que toutes les entités gérées par le PostgresRepository
    possèdent un attribut 'id'. Il sert de contrainte de type pour assurer que seules les classes
    avec un identifiant peuvent être utilisées avec le repository.
    
    Attributes:
        id (int): L'identifiant unique de l'entité
    """
    id: int

T = TypeVar('T', bound=HasId)

class PostgresRepository(Repository[T]):
    def __init__(self, entity_type: Type[T]):
        self._entity_type = entity_type
        self._db: Optional[AsyncSession] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """S'assure que la base de données est initialisée"""
        if not self._initialized:
            if not async_session:
                config = load_config()
                await init_db(config.database)
            self._initialized = True
    
    @asynccontextmanager
    async def _get_session(self):
        """Récupère une session de base de données dans un contexte"""
        await self._ensure_initialized()
        
        if self._db is not None:
            yield self._db
        else:
            session = await get_session()
            try:
                yield session
            finally:
                await session.close()

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

    async def get_all(self):
        async with get_session() as session:
            query = select(self._entity_type)
            result = await session.execute(query)
            return result.scalars().all()

    async def add(self, entity: T) -> T:
        async with get_session() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def get_by_id(self, id: int) -> Optional[T]:
        async with get_session() as session:
            result = await session.get(self._entity_type, id)
            return result

    async def delete(self, entity: T) -> None:
        async with get_session() as session:
            await session.delete(entity)
            await session.commit() 