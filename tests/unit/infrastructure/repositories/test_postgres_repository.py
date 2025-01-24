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

@pytest.mark.asyncio
async def test_postgres_repository_get():
    # Arrange
    mock_db = Mock()
    mock_query = Mock()
    mock_filter = Mock()
    mock_user = User(username="test_user", email="test@example.com")
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_user
    
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = PostgresRepository(User)
        
        # Act
        result = await repo.get("test_id")
        
        # Assert
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_get_not_found():
    # Arrange
    mock_db = Mock()
    mock_query = Mock()
    mock_filter = Mock()
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = None
    
    with patch('src.infrastructure.repositories.postgres_repository.get_db', return_value=iter([mock_db])):
        repo = PostgresRepository(User)
        
        # Act
        result = await repo.get("test_id")
        
        # Assert
        assert result is None
        mock_db.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once() 