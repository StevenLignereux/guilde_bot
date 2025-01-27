import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.domain.entities.task import Task

@pytest.mark.asyncio
async def test_postgres_repository_save():
    """Test la sauvegarde d'une entité"""
    # Arrange
    mock_db = AsyncMock()
    mock_entity = Task(description="Test task")
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    await repo.save(mock_entity)
    
    # Assert
    mock_db.add.assert_called_once_with(mock_entity)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_entity)

@pytest.mark.asyncio
async def test_postgres_repository_save_failure():
    """Test la gestion des erreurs lors de la sauvegarde"""
    # Arrange
    mock_db = AsyncMock()
    mock_entity = Task(description="Test task")
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    # Act & Assert
    repo = PostgresRepository(Task)
    repo.db = mock_db
    with pytest.raises(SQLAlchemyError):
        await repo.save(mock_entity)
    
    mock_db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_get():
    """Test la récupération d'une entité"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_task = Task(id=1, description="Test task")
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    result = await repo.get(1)
    
    # Assert
    assert result == mock_task
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_get_not_found():
    """Test la récupération d'une entité inexistante"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    result = await repo.get(999)
    
    # Assert
    assert result is None
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_update():
    """Test la mise à jour d'une entité"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_task = Task(id=1, description="Test task")
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    mock_task.description = "Updated task"
    result = await repo.update(mock_task)
    
    # Assert
    assert result.description == "Updated task"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_task)

@pytest.mark.asyncio
async def test_postgres_repository_update_not_found():
    """Test la mise à jour d'une entité inexistante"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    task = Task(id=999, description="Test task")
    
    # Assert
    with pytest.raises(ValueError, match="L'entité avec l'ID 999 n'existe pas"):
        await repo.update(task)

@pytest.mark.asyncio
async def test_postgres_repository_update_error():
    """Test la gestion des erreurs lors de la mise à jour"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_task = Task(id=1, description="Test task")
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    
    # Assert
    with pytest.raises(SQLAlchemyError):
        await repo.update(mock_task)
    mock_db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_delete():
    """Test la suppression d'une entité"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_task = Task(id=1, description="Test task")
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    await repo.delete(1)
    
    # Assert
    mock_db.delete.assert_called_once_with(mock_task)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_postgres_repository_delete_not_found():
    """Test la suppression d'une entité inexistante"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    
    # Assert
    with pytest.raises(ValueError, match="L'entité avec l'ID 999 n'existe pas"):
        await repo.delete(999)

@pytest.mark.asyncio
async def test_postgres_repository_delete_error():
    """Test la gestion des erreurs lors de la suppression"""
    # Arrange
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_task = Task(id=1, description="Test task")
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    mock_db.commit.side_effect = SQLAlchemyError("Test error")
    
    # Act
    repo = PostgresRepository(Task)
    repo.db = mock_db
    
    # Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete(1)
    mock_db.rollback.assert_called_once() 