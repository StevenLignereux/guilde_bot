from abc import ABC, abstractmethod

class EntityFactory(ABC):
    @abstractmethod
    def create(self):
        pass 