import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.domain.entities.task import TaskList, Task
from src.infrastructure.repositories.task_repository import TaskRepository
from sqlalchemy.exc import SQLAlchemyError
import logging

@pytest.mark.asyncio
async def test_create_list():
    """Test la création d'une liste de tâches"""
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session
    
    # Act
    task_list = await repo.create_list(123, "Test List")
    
    # Assert
    assert task_list.name == "Test List"
    assert task_list.user_discord_id == 123
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(task_list)

@pytest.mark.asyncio
async def test_get_user_lists():
    # Arrange
    repo = TaskRepository()
    user_id = "123456789"
    mock_lists = [
        TaskList(name="List 1", user_discord_id=user_id),
        TaskList(name="List 2", user_discord_id=user_id)
    ]
    
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.unique = Mock(return_value=mock_result)
    mock_result.scalars = Mock(return_value=mock_result)
    mock_result.all = Mock(return_value=mock_lists)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session
    
    # Act
    lists = await repo.get_user_lists(user_id)
    
    # Assert
    assert len(lists) == 2
    assert all(lst.user_discord_id == user_id for lst in lists)
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_list_duplicate_name():
    """Test la création d'une liste avec un nom déjà utilisé"""
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = TaskList(name="Test List", user_discord_id=123)
    mock_session.execute.return_value = mock_result
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="Une liste avec ce nom existe déjà"):
        await repo.create_list("Test List", 123)

@pytest.mark.asyncio
async def test_add_task_success():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    repo.db = mock_session

    # Act
    task = await repo.add_task("Test Task", 1)

    # Assert
    assert task.description == "Test Task"
    assert task.task_list_id == 1
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_toggle_task_success():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)
    
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=task)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session

    # Act
    result = await repo.toggle_task(1)

    # Assert
    assert result.completed == True
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_lists_error():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.get_user_lists("123456789")

@pytest.mark.asyncio
async def test_toggle_task_not_found():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session

    # Act
    result = await repo.toggle_task(999)  # ID inexistant

    # Assert
    assert result is None
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()

@pytest.mark.asyncio
async def test_add_task_with_invalid_list_id():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.add_task("Test Task", 999)  # ID de liste inexistant

@pytest.mark.asyncio
async def test_add_multiple_tasks_to_list():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    repo.db = mock_session

    # Act
    task1 = await repo.add_task("Task 1", 1)
    task2 = await repo.add_task("Task 2", 1)

    # Assert
    assert task1.description == "Task 1"
    assert task2.description == "Task 2"
    assert mock_session.add.call_count == 2
    assert mock_session.commit.call_count == 2

@pytest.mark.asyncio
async def test_create_list_sql_error(caplog):
    """Test la gestion des erreurs SQL lors de la création d'une liste"""
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    mock_session.rollback = AsyncMock()
    repo.db = mock_session

    # Configurer la capture des logs
    caplog.set_level(logging.ERROR)

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.create_list(123, "Test List")
    
    mock_session.rollback.assert_called_once()
    assert "Erreur lors de la création de la liste" in caplog.text

@pytest.mark.asyncio
async def test_add_task_sql_error():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    mock_session.rollback = AsyncMock()
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.add_task("Test Task", 1)
    
    mock_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_toggle_task_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)
    
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=task)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    mock_session.rollback = AsyncMock()
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.toggle_task(1)
    
    mock_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_update_task_description_not_found():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="La tâche avec l'ID 999 n'existe pas"):
        await repo.update_task_description(999, "Nouvelle description")

@pytest.mark.asyncio
async def test_delete_list_with_tasks():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")
    tasks = [
        Task(id=1, description="Task 1", task_list_id=list_id),
        Task(id=2, description="Task 2", task_list_id=list_id)
    ]

    mock_session = AsyncMock()
    mock_list_result = AsyncMock()
    mock_list_result.scalar_one_or_none = Mock(return_value=task_list)
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars = Mock(return_value=mock_tasks_result)
    mock_tasks_result.all = Mock(return_value=tasks)

    mock_session.execute = AsyncMock(side_effect=[mock_list_result, mock_tasks_result])
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()
    repo.db = mock_session

    # Act
    result = await repo.delete_list(list_id)

    # Assert
    assert result is True
    assert mock_session.delete.call_count == 3  # 2 tasks + 1 list
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_list_not_found():
    """Test la suppression d'une liste inexistante"""
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="La liste avec l'ID 999 n'existe pas"):
        await repo.delete_list(999)

@pytest.mark.asyncio
async def test_delete_list_sql_error_during_commit():
    """Test la gestion des erreurs SQL lors de la suppression d'une liste"""
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")
    
    mock_session = AsyncMock()
    mock_list_result = AsyncMock()
    mock_list_result.scalar_one_or_none.return_value = task_list
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars.return_value.all.return_value = []
    
    mock_session.execute.side_effect = [mock_list_result, mock_tasks_result]
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete_list(list_id)

@pytest.mark.asyncio
async def test_delete_task_not_found():
    # Arrange
    repo = TaskRepository()
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match="La tâche avec l'ID 999 n'existe pas"):
        await repo.delete_task(999)

@pytest.mark.asyncio
async def test_delete_task_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")
    
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=task)
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Test error"))
    mock_session.rollback = AsyncMock()
    repo.db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete_task(1)
    
    mock_session.rollback.assert_called_once() 