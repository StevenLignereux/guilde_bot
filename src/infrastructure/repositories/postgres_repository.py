from typing import Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from src.domain.interfaces.repository import Repository
from src.infrastructure.config.database import get_db

T = TypeVar('T')

class PostgresRepository(Repository[T]):
    def __init__(self, model_class):
        self.model_class = model_class
        self.db: Session = next(get_db())

    async def get(self, id: str) -> Optional[T]:
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()

    async def save(self, entity: T) -> None:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity) 