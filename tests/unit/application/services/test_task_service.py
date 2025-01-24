import pytest
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO
import sys
import logging
from src.application.services.task_service import TaskService
from src.domain.entities.task import Task, TaskList

@pytest.mark.asyncio
async def test_create_list_success():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task_list = TaskList(name="Test List", user_discord_id="123456789")
        mock_instance.create_list = AsyncMock(return_value=mock_task_list)
        service.repository = mock_instance
        
        # Act
        success, message, task_list = await service.create_list("Test List", "123456789")
        
        # Assert
        assert success is True
        assert task_list is not None
        assert task_list.name == "Test List"
        mock_instance.create_list.assert_called_once()

@pytest.mark.asyncio
async def test_create_list_empty_name():
    # Arrange
    service = TaskService()
    
    # Act
    success, message, task_list = await service.create_list("", "123456789")
    
    # Assert
    assert success is False
    assert "ne peut pas être vide" in message
    assert task_list is None

@pytest.mark.asyncio
async def test_create_list_too_long_name():
    # Arrange
    service = TaskService()
    long_name = "x" * 101  # Crée une chaîne de 101 caractères
    
    # Act
    success, message, task_list = await service.create_list(long_name, "123456789")
    
    # Assert
    assert success is False
    assert "trop long" in message
    assert task_list is None

@pytest.mark.asyncio
async def test_get_user_lists():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_lists = [
            TaskList(name="List 1", user_discord_id="123456789"),
            TaskList(name="List 2", user_discord_id="123456789")
        ]
        mock_instance.get_user_lists = AsyncMock(return_value=mock_lists)
        service.repository = mock_instance
        
        # Act
        lists = await service.get_user_lists("123456789")
        
        # Assert
        assert len(lists) == 2
        mock_instance.get_user_lists.assert_called_once_with("123456789")

@pytest.mark.asyncio
async def test_get_user_lists_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.get_user_lists = AsyncMock(side_effect=Exception("Erreur de récupération des listes"))
        service.repository = mock_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Erreur de récupération des listes"):
            await service.get_user_lists("123456789")

@pytest.mark.asyncio
async def test_add_task():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task = Task(description="Test Task", task_list_id=1)
        mock_instance.add_task = AsyncMock(return_value=mock_task)
        service.repository = mock_instance
        
        # Act
        task = await service.add_task("Test Task", 1)
        
        # Assert
        assert task.description == "Test Task"
        mock_instance.add_task.assert_called_once_with("Test Task", 1)

@pytest.mark.asyncio
async def test_toggle_task():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task = Task(description="Test Task", completed=False)
        mock_instance.toggle_task = AsyncMock(return_value=mock_task)
        service.repository = mock_instance
        
        # Act
        task = await service.toggle_task(1)
        
        # Assert
        assert task is not None
        mock_instance.toggle_task.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_create_list_with_exception(caplog):
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        error_message = "Erreur inattendue de test"
        mock_instance.create_list = AsyncMock(side_effect=RuntimeError(error_message))
        service.repository = mock_instance
        
        # Configurer la capture des logs
        caplog.set_level(logging.ERROR)
        
        # Act
        success, message, task_list = await service.create_list("Test List", "123456789")
        
        # Assert
        assert success is False
        assert "Une erreur est survenue" in message
        assert task_list is None
        # Vérifier que l'erreur a été loggée
        assert "Erreur inattendue lors de la création de la liste" in caplog.text
        assert error_message in caplog.text

@pytest.mark.asyncio
async def test_check_database_success():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task_list = TaskList(name="__test__", user_discord_id="__test__")
        mock_instance.create_list = AsyncMock(return_value=mock_task_list)
        
        # Créer un mock pour db qui retourne des coroutines
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_instance.db = mock_db
        
        service.repository = mock_instance
        
        # Act
        success, message = await service.check_database()
        
        # Assert
        assert success is True
        assert "Base de données opérationnelle" in message
        mock_instance.db.delete.assert_awaited_once_with(mock_task_list)
        mock_instance.db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_check_database_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.create_list = AsyncMock(side_effect=Exception("Test error"))
        service.repository = mock_instance
        
        # Act
        success, message = await service.check_database()
        
        # Assert
        assert success is False
        assert "Erreur de base de données" in message

@pytest.mark.asyncio
async def test_check_database_none_result():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.create_list = AsyncMock(return_value=None)
        service.repository = mock_instance
        
        # Act
        result = await service.check_database()  # On ne fait pas de unpacking ici
        
        # Assert
        assert result[0] is False  # Premier élément du tuple
        assert "Erreur de base de données" in result[1]  # Deuxième élément du tuple 

@pytest.mark.asyncio
async def test_add_task_to_existing_list():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task = Task(description="Test Task", task_list_id=1)
        mock_instance.add_task = AsyncMock(return_value=mock_task)
        service.repository = mock_instance
        
        # Act
        task = await service.add_task("Test Task", 1)
        
        # Assert
        assert task is not None
        assert task.description == "Test Task"
        assert task.task_list_id == 1
        mock_instance.add_task.assert_called_once_with("Test Task", 1)

@pytest.mark.asyncio
async def test_add_task_with_invalid_list():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.add_task = AsyncMock(side_effect=Exception("Liste invalide"))
        service.repository = mock_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Liste invalide"):
            await service.add_task("Test Task", 999)  # ID de liste invalide 

@pytest.mark.asyncio
async def test_create_list_unexpected_error():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.create_list = AsyncMock(side_effect=RuntimeError("Erreur inattendue"))
        service.repository = mock_instance
        
        # Act
        success, message, task_list = await service.create_list("Test List", "123456789")
        
        # Assert
        assert success is False
        assert "Une erreur est survenue" in message
        assert task_list is None
        mock_instance.create_list.assert_called_once() 

@pytest.mark.asyncio
async def test_check_database_delete_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task_list = TaskList(name="__test__", user_discord_id="__test__")
        mock_instance.create_list = AsyncMock(return_value=mock_task_list)
        
        # Créer un mock pour db qui simule une erreur lors de la suppression
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock(side_effect=Exception("Erreur de suppression"))
        mock_instance.db = mock_db
        
        service.repository = mock_instance
        
        # Act
        success, message = await service.check_database()
        
        # Assert
        assert success is False
        assert "Erreur de base de données" in message
        assert "Erreur de suppression" in message
        mock_instance.db.delete.assert_awaited_once_with(mock_task_list) 

@pytest.mark.asyncio
async def test_check_database_commit_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_task_list = TaskList(name="__test__", user_discord_id="__test__")
        mock_instance.create_list = AsyncMock(return_value=mock_task_list)
        
        # Créer un mock pour db qui simule une erreur lors du commit
        mock_db = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock(side_effect=Exception("Erreur de commit"))
        mock_instance.db = mock_db
        
        service.repository = mock_instance
        
        # Act
        success, message = await service.check_database()
        
        # Assert
        assert success is False
        assert "Erreur de base de données" in message
        assert "Erreur de commit" in message
        mock_instance.db.delete.assert_awaited_once_with(mock_task_list)
        mock_instance.db.commit.assert_awaited_once() 

@pytest.mark.asyncio
async def test_add_task_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.add_task = AsyncMock(side_effect=Exception("Erreur d'ajout de tâche"))
        service.repository = mock_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Erreur d'ajout de tâche"):
            await service.add_task("Test Task", 1)

@pytest.mark.asyncio
async def test_toggle_task_failure():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.toggle_task = AsyncMock(side_effect=Exception("Erreur de basculement de tâche"))
        service.repository = mock_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="Erreur de basculement de tâche"):
            await service.toggle_task(1) 

@pytest.mark.asyncio
async def test_check_database_create_returns_none():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        mock_instance.create_list = AsyncMock(return_value=None)
        service.repository = mock_instance
        
        # Act
        success, message = await service.check_database()
        
        # Assert
        assert success is False
        assert "impossible de créer une liste de test" in message 

@pytest.mark.asyncio
async def test_create_list_value_error():
    # Arrange
    with patch('src.infrastructure.repositories.task_repository.TaskRepository') as mock_repo:
        service = TaskService()
        mock_instance = AsyncMock()
        error_message = "Liste déjà existante"
        mock_instance.create_list = AsyncMock(side_effect=ValueError(error_message))
        service.repository = mock_instance
        
        # Act
        success, message, task_list = await service.create_list("Test List", "123456789")
        
        # Assert
        assert success is False
        assert message == error_message
        assert task_list is None 

@pytest.mark.asyncio
async def test_create_list_whitespace_name():
    # Arrange
    service = TaskService()
    
    # Act
    success, message, task_list = await service.create_list("   ", "123456789")
    
    # Assert
    assert success is False
    assert "ne peut pas être vide" in message
    assert task_list is None 