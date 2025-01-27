import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.domain.entities.task import TaskList, Task
from src.infrastructure.repositories.task_repository import TaskRepository
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from unittest import mock

@pytest.mark.asyncio
async def test_create_list():
    """Test la création d'une liste de tâches"""
    # Arrange
    repo = TaskRepository()
    name = "Test List"
    user_discord_id = "123456789"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.create_list(name, user_discord_id)

    # Assert
    assert str(result.name) == name
    assert str(result.user_discord_id) == user_discord_id
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_user_lists():
    # Arrange
    repo = TaskRepository()
    user_discord_id = "123456789"
    mock_lists = [
        TaskList(name="List 1", user_discord_id=user_discord_id),
        TaskList(name="List 2", user_discord_id=user_discord_id)
    ]

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = mock_lists
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.get_user_lists(user_discord_id)

    # Assert
    assert len(result) == 2
    assert all(isinstance(item, TaskList) for item in result)
    mock_session.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_list_duplicate_name():
    """Test la création d'une liste avec un nom déjà utilisé"""
    # Arrange
    repo = TaskRepository()
    name = "Test List"
    user_discord_id = "123456789"
    existing_list = TaskList(name=name, user_discord_id=user_discord_id)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = existing_list
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"Une liste avec le nom '{name}' existe déjà"):
        await repo.create_list(name, user_discord_id)

@pytest.mark.asyncio
async def test_add_task_success():
    # Arrange
    repo = TaskRepository()
    description = "Test Task"
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task_list
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.add_task(description, list_id)

    # Assert
    assert str(result.description) == description
    assert int(result.task_list_id) == list_id
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_toggle_task_success():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.toggle_task(1)

    # Assert
    assert result is not None
    assert result.completed is True
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_user_lists_error():
    # Arrange
    repo = TaskRepository()
    user_discord_id = "123456789"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.get_user_lists(user_discord_id)

@pytest.mark.asyncio
async def test_toggle_task_not_found():
    # Arrange
    repo = TaskRepository()
    task_id = 999

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"La tâche avec l'ID {task_id} n'existe pas"):
        await repo.toggle_task(task_id)

@pytest.mark.asyncio
async def test_add_task_with_invalid_list_id():
    # Arrange
    repo = TaskRepository()
    description = "Test Task"
    list_id = 999

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"La liste avec l'ID {list_id} n'existe pas"):
        await repo.add_task(description, list_id)

@pytest.mark.asyncio
async def test_add_multiple_tasks_to_list():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")
    descriptions = ["Task 1", "Task 2", "Task 3"]

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task_list
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    tasks = []
    for description in descriptions:
        task = await repo.add_task(description, list_id)
        tasks.append(task)

    # Assert
    assert len(tasks) == 3
    assert all(task.task_list_id == list_id for task in tasks)
    assert all(not task.completed for task in tasks)
    assert all(isinstance(task.description, str) for task in tasks)
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_create_list_sql_error():
    # Arrange
    repo = TaskRepository()
    name = "Test List"
    user_discord_id = "123456789"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.create_list(name, user_discord_id)
    mock_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_task_sql_error():
    # Arrange
    repo = TaskRepository()
    description = "Test Task"
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task_list
    mock_session.execute.return_value = mock_result
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.add_task(description, list_id)
    mock_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_toggle_task_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task
    mock_session.execute.return_value = mock_result
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.toggle_task(1)
    mock_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_task_description_not_found():
    # Arrange
    repo = TaskRepository()
    task_id = 999
    new_description = "Updated Task"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"La tâche avec l'ID {task_id} n'existe pas"):
        await repo.update_task_description(task_id, new_description)

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

    mock_session = AsyncMock(spec=AsyncSession)
    mock_list_result = AsyncMock()
    mock_list_result.scalar_one_or_none.return_value = task_list
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars.return_value.all.return_value = tasks
    mock_session.execute.side_effect = [mock_list_result, mock_tasks_result]
    repo._db = mock_session

    # Act
    await repo.delete_list(list_id)

    # Assert
    mock_session.delete.assert_has_awaits([mock.call(task) for task in tasks] + [mock.call(task_list)])
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_list_not_found():
    """Test la suppression d'une liste inexistante"""
    # Arrange
    repo = TaskRepository()
    list_id = 999

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"La liste avec l'ID {list_id} n'existe pas"):
        await repo.delete_list(list_id)

@pytest.mark.asyncio
async def test_delete_task_not_found():
    # Arrange
    repo = TaskRepository()
    task_id = 999

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(ValueError, match=f"La tâche avec l'ID {task_id} n'existe pas"):
        await repo.delete_task(task_id)

@pytest.mark.asyncio
async def test_delete_task_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task
    mock_session.execute.return_value = mock_result
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete_task(1)
    mock_session.rollback.assert_awaited_once() 