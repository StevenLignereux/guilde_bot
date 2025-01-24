from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        pass  # pragma: no cover

    @abstractmethod
    async def save(self, entity: T) -> None:
        pass  # pragma: no cover 