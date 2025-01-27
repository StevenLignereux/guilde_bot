import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from src.infrastructure.commands.task_commands import TaskCommands
from src.domain.entities.task import Task, TaskList

@pytest.fixture
def mock_interaction():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.id = "123456789"
    return interaction

@pytest.mark.asyncio
async def test_toggle_task_success():
    """Test le marquage d'une tâche comme effectuée avec succès"""
    # Arrange
    mock_task_service = AsyncMock()
    mock_task = Task(id=1, description="Test task", completed=False)
    mock_task_service.toggle_task.return_value = mock_task
    
    cog = TaskCommands(MagicMock())
    cog.task_service = mock_task_service
    
    mock_interaction = AsyncMock()
    mock_interaction.response.send_message = AsyncMock()
    
    # Act
    await cog.toggle_task(mock_interaction, 1)
    
    # Assert
    mock_task_service.toggle_task.assert_called_once_with(1)
    mock_interaction.response.send_message.assert_called_once_with(
        "✅ La tâche a été marquée comme effectuée !"
    )

@pytest.mark.asyncio
async def test_toggle_task_already_completed():
    """Test le marquage d'une tâche déjà effectuée"""
    # Arrange
    mock_task_service = AsyncMock()
    mock_task = Task(id=1, description="Test task", completed=True)
    mock_task_service.toggle_task.return_value = mock_task
    
    cog = TaskCommands(MagicMock())
    cog.task_service = mock_task_service
    
    mock_interaction = AsyncMock()
    mock_interaction.response.send_message = AsyncMock()
    
    # Act
    await cog.toggle_task(mock_interaction, 1)
    
    # Assert
    mock_task_service.toggle_task.assert_called_once_with(1)
    mock_interaction.response.send_message.assert_called_once_with(
        "❌ La tâche a été marquée comme non effectuée !"
    )

@pytest.mark.asyncio
async def test_toggle_task_not_found():
    """Test le marquage d'une tâche inexistante"""
    # Arrange
    mock_task_service = AsyncMock()
    mock_task_service.toggle_task.return_value = None
    
    cog = TaskCommands(MagicMock())
    cog.task_service = mock_task_service
    
    mock_interaction = AsyncMock()
    mock_interaction.response.send_message = AsyncMock()
    
    # Act
    await cog.toggle_task(mock_interaction, 999)
    
    # Assert
    mock_task_service.toggle_task.assert_called_once_with(999)
    mock_interaction.response.send_message.assert_called_once_with(
        "❌ La tâche n'a pas été trouvée !"
    ) 