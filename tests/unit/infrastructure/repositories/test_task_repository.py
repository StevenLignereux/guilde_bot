import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.domain.entities.task import TaskList, Task
from src.infrastructure.repositories.task_repository import TaskRepository
from sqlalchemy.exc import SQLAlchemyError
import logging

@pytest.mark.asyncio
async def test_create_list(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Act
    task_list = await repo.create_list("Test List", "123456789")
    
    # Assert
    assert task_list.name == "Test List"
    assert task_list.user_discord_id == "123456789"
    assert task_list.id is not None

@pytest.mark.asyncio
async def test_get_user_lists(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    user_id = "123456789"
    
    # Create some test data
    task_list1 = TaskList(name="List 1", user_discord_id=user_id)
    task_list2 = TaskList(name="List 2", user_discord_id=user_id)
    test_session.add(task_list1)
    test_session.add(task_list2)
    test_session.commit()
    
    # Act
    lists = await repo.get_user_lists(user_id)
    
    # Assert
    assert len(lists) == 2
    assert all(lst.user_discord_id == user_id for lst in lists)

@pytest.mark.asyncio
async def test_create_list_duplicate_name(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Act & Assert
    await repo.create_list("Test List", "123456789")
    with pytest.raises(ValueError, match="existe déjà"):
        await repo.create_list("Test List", "123456789")

@pytest.mark.asyncio
async def test_add_task_success(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    task_list = TaskList(name="Test List", user_discord_id="123456789")
    test_session.add(task_list)
    test_session.commit()
    
    # Act
    task = await repo.add_task("Test Task", task_list.id)
    
    # Assert
    assert task.description == "Test Task"
    assert task.task_list_id == task_list.id

@pytest.mark.asyncio
async def test_toggle_task_success(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    task = Task(description="Test Task", completed=False)
    test_session.add(task)
    test_session.commit()
    
    # Act
    updated_task = await repo.toggle_task(task.id)
    
    # Assert
    assert updated_task.completed is True

@pytest.mark.asyncio
async def test_get_user_lists_error(test_session, caplog):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Configurer la capture des logs
    caplog.set_level(logging.ERROR)
    
    # Simuler une erreur SQL
    error_message = "Test error"
    with patch.object(test_session, 'query', side_effect=SQLAlchemyError(error_message)):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await repo.get_user_lists("123456789")
        
        # Vérifier que l'erreur a été loggée
        assert "Erreur lors de la récupération des listes" in caplog.text
        assert error_message in caplog.text

@pytest.mark.asyncio
async def test_toggle_task_not_found(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Act
    result = await repo.toggle_task(999)  # ID inexistant
    
    # Assert
    assert result is None

@pytest.mark.asyncio
async def test_add_task_with_invalid_list_id(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Act & Assert
    with pytest.raises(ValueError, match="La liste avec l'ID 999 n'existe pas"):
        await repo.add_task("Test Task", 999)  # ID de liste inexistant

@pytest.mark.asyncio
async def test_add_multiple_tasks_to_list(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    task_list = TaskList(name="Test List", user_discord_id="123456789")
    test_session.add(task_list)
    test_session.commit()
    
    # Act
    task1 = await repo.add_task("Task 1", task_list.id)
    task2 = await repo.add_task("Task 2", task_list.id)
    
    # Assert
    assert task1.description == "Task 1"
    assert task2.description == "Task 2"
    assert task1.task_list_id == task_list.id
    assert task2.task_list_id == task_list.id
    
    # Vérifier que les tâches sont bien dans la liste
    tasks = test_session.query(Task).filter(Task.task_list_id == task_list.id).all()
    assert len(tasks) == 2

@pytest.mark.asyncio
async def test_create_list_sql_error(test_session, caplog):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Configurer la capture des logs
    caplog.set_level(logging.ERROR)
    
    # Simuler une erreur SQL lors de l'ajout
    error_message = "Test error"
    with patch.object(test_session, 'add', side_effect=SQLAlchemyError(error_message)):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await repo.create_list("Test List", "123456789")
        
        # Vérifier que l'erreur a été loggée
        assert "Erreur lors de la création de la liste" in caplog.text
        assert error_message in caplog.text

@pytest.mark.asyncio
async def test_add_task_sql_error(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    task_list = TaskList(name="Test List", user_discord_id="123456789")
    test_session.add(task_list)
    test_session.commit()
    
    # Simuler une erreur SQL lors de l'ajout de la tâche
    with patch.object(test_session, 'add', side_effect=SQLAlchemyError("Test error")):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await repo.add_task("Test Task", task_list.id)

@pytest.mark.asyncio
async def test_toggle_task_sql_error(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    task = Task(description="Test Task", completed=False)
    test_session.add(task)
    test_session.commit()
    
    # Simuler une erreur SQL lors de la mise à jour
    with patch.object(test_session, 'commit', side_effect=SQLAlchemyError("Test error")):
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            await repo.toggle_task(task.id)

@pytest.mark.asyncio
async def test_update_task_description_not_found():
    # Arrange
    repo = TaskRepository()
    task_id = 999

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match=f"La tâche avec l'ID {task_id} n'existe pas"):
        await repo.update_task_description(task_id, "Nouvelle description")

@pytest.mark.asyncio
async def test_update_task_description_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Ancienne description")

    # Mock de la session avec une erreur SQL
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task
    repo.db.commit.side_effect = SQLAlchemyError("Erreur SQL")

    # Act & Assert
    with pytest.raises(Exception):
        await repo.update_task_description(1, "Nouvelle description")
    repo.db.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_delete_list_with_tasks():
    # Arrange
    repo = TaskRepository()
    list_id = 1
    task_list = TaskList(id=list_id, name="Test List")

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task_list

    # Act
    result = await repo.delete_list(list_id)

    # Assert
    assert result is True
    repo.db.query.return_value.filter.return_value.delete.assert_called_once()  # Vérifier que les tâches sont supprimées
    repo.db.delete.assert_called_once_with(task_list)  # Vérifier que la liste est supprimée
    repo.db.commit.assert_called_once()

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
async def test_delete_task_success():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task

    # Act
    result = await repo.delete_task(1)

    # Assert
    assert result is True
    repo.db.delete.assert_called_once_with(task)
    repo.db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_task_not_found():
    # Arrange
    repo = TaskRepository()
    task_id = 999

    # Mock de la session
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match=f"La tâche avec l'ID {task_id} n'existe pas"):
        await repo.delete_task(task_id)

@pytest.mark.asyncio
async def test_delete_task_sql_error():
    # Arrange
    repo = TaskRepository()
    task = Task(id=1, description="Test Task")

    # Mock de la session avec une erreur SQL
    repo.db = Mock()
    repo.db.query.return_value.filter.return_value.first.return_value = task
    repo.db.commit.side_effect = SQLAlchemyError("Erreur SQL")

    # Act
    result = await repo.delete_task(1)

    # Assert
    assert result is False
    repo.db.rollback.assert_called_once() 