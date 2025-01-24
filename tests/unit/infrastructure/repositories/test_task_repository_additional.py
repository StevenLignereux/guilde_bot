import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from src.domain.entities.task import Task, TaskList
from src.infrastructure.repositories.task_repository import TaskRepository

@pytest.mark.asyncio
async def test_delete_list_sql_error_during_task_deletion():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    # Mock de la session avec une erreur SQL lors de la suppression des tâches
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task_list
    repo.db.query.return_value.filter.return_value.delete.side_effect = SQLAlchemyError("Erreur SQL")

    # Act
    result = await repo.delete_list(list_id)

    # Assert
    assert result is False
    repo.db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_toggle_task_with_refresh():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task

    # Act
    result = await repo.toggle_task(1)

    # Assert
    assert result is task
    assert result.completed is True
    repo.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_task_description_success():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Ancienne description")
    new_description = "Nouvelle description"

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task

    # Act
    result = await repo.update_task_description(1, new_description)

    # Assert
    assert result is task
    assert result.description == new_description
    repo.db.commit.assert_called_once()
    repo.db.refresh.assert_called_once_with(task)

@pytest.mark.asyncio
async def test_delete_list_not_found():
    # Arrange
    repo = TaskRepository()
    list_id = 999

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match=f"La liste avec l'ID {list_id} n'existe pas"):
        await repo.delete_list(list_id)

@pytest.mark.asyncio
async def test_delete_list_sql_error_during_commit():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    # Mock de la session avec une erreur SQL lors du commit
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task_list
    repo.db.commit.side_effect = SQLAlchemyError("Erreur SQL")

    # Act
    result = await repo.delete_list(list_id)

    # Assert
    assert result is False
    repo.db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_toggle_task_sql_error_with_rollback():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task", completed=False)

    # Mock de la session avec une erreur SQL lors du commit
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task
    repo.db.commit.side_effect = SQLAlchemyError("Erreur SQL")

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.toggle_task(1)
    repo.db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_update_task_description_sql_error_with_rollback():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")

    # Mock de la session avec une erreur SQL lors du commit
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task
    repo.db.commit.side_effect = SQLAlchemyError("Erreur SQL")

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.update_task_description(1, "Nouvelle description")
    repo.db.rollback.assert_called_once() 