import pytest
from src.domain.interfaces.repository import Repository

def test_repository_is_abstract():
    # Vérifier qu'on ne peut pas instancier directement Repository
    with pytest.raises(TypeError):
        Repository()

def test_repository_methods_are_abstract():
    # Créer une classe qui hérite de Repository sans implémenter les méthodes
    class InvalidRepo(Repository):
        pass
    
    with pytest.raises(TypeError):
        InvalidRepo()

@pytest.mark.asyncio
async def test_repository_implementation():
    # Créer une classe qui implémente correctement Repository
    class ValidRepo(Repository):
        async def get(self, id: str):
            return "test_entity"
            
        async def save(self, entity):
            self.saved_entity = entity
    
    # Vérifier qu'on peut instancier la classe
    repo = ValidRepo()
    assert isinstance(repo, Repository)
    
    # Vérifier que les méthodes fonctionnent
    result = await repo.get("test_id")
    assert result == "test_entity"
    
    await repo.save("test_entity")
    assert repo.saved_entity == "test_entity" 