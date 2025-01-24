import pytest
from unittest.mock import Mock, patch
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.domain.entities.user import User

@pytest.mark.asyncio
async def test_postgres_repository_save():
    # Arrange
    mock_db = Mock()
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = PostgresRepository(User)
        user = User(username="test_user", email="test@example.com")
        
        # Act
        await repo.save(user)
        
        # Assert
        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user) 