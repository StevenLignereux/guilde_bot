import pytest
from unittest.mock import Mock, patch
from src.domain.entities.task import TaskList, Task
from src.infrastructure.repositories.task_repository import TaskRepository

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
async def test_get_user_lists_error(test_session):
    # Arrange
    repo = TaskRepository()
    repo.db = test_session
    
    # Simuler une erreur SQL
    with patch.object(test_session, 'query', side_effect=Exception("Test error")):
        # Act & Assert
        with pytest.raises(Exception):
            await repo.get_user_lists("123456789")

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