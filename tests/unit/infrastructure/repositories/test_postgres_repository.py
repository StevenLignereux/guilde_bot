import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError
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

@pytest.mark.asyncio
async def test_postgres_repository_save_failure():
    # Arrange
    mock_db = Mock()
    mock_entity = Mock()
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = PostgresRepository(Mock)
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await repo.save(mock_entity)
            
        mock_db.add.assert_called_once_with(mock_entity)
        mock_db.commit.assert_called_once() 