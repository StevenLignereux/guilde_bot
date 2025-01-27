import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from src.domain.entities.task import Task, TaskList
from src.infrastructure.repositories.task_repository import TaskRepository
import logging
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_delete_list_sql_error_during_task_deletion():
    """Test la gestion des erreurs SQL lors de la suppression des tâches d'une liste"""
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    # Mock de la session avec une erreur SQL lors de la suppression des tâches
    mock_session = AsyncMock(spec=AsyncSession)
    mock_list_result = AsyncMock()
    mock_list_result.scalar_one_or_none.return_value = task_list
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars.return_value.all.return_value = []
    
    mock_session.execute.side_effect = [mock_list_result, SQLAlchemyError("Test error")]
    repo._db = cast(AsyncSession, mock_session)

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete_list(list_id)

@pytest.mark.asyncio
async def test_toggle_task_with_refresh():
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
    mock_session.refresh.assert_awaited_once_with(task)

@pytest.mark.asyncio
async def test_update_task_description_success():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Ancienne description")
    new_description = "Nouvelle description"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.update_task_description(1, new_description)

    # Assert
    assert result is not None
    assert str(result.description) == new_description
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(task)

@pytest.mark.asyncio
async def test_delete_list_not_found():
    # Arrange
    repo = TaskRepository()
    list_id = 999

    # Mock de la session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    repo._db = mock_session

    # Act
    result = await repo.delete_list(list_id)

    # Assert
    assert result is False
    mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_delete_list_sql_error_during_commit():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    mock_session = AsyncMock(spec=AsyncSession)
    mock_list_result = AsyncMock()
    mock_list_result.scalar_one_or_none.return_value = task_list
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars.return_value.all.return_value = []
    mock_session.execute.side_effect = [mock_list_result, mock_tasks_result]
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.delete_list(list_id)
    mock_session.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_toggle_task_sql_error_with_rollback():
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
async def test_update_task_description_sql_error_with_rollback():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")
    new_description = "Updated description"

    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = task
    mock_session.execute.return_value = mock_result
    mock_session.commit.side_effect = SQLAlchemyError("Test error")
    repo._db = mock_session

    # Act & Assert
    with pytest.raises(SQLAlchemyError):
        await repo.update_task_description(1, new_description)
    mock_session.rollback.assert_awaited_once() 