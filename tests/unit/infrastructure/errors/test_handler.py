import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.errors.handler import ErrorHandler
from src.infrastructure.errors.exceptions import (
    ConfigurationError, DatabaseError, DiscordError,
    CommandError, ResourceError, APIError,
    ValidationError, PermissionError
)

@pytest.fixture
def error_handler():
    return ErrorHandler()

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    return ctx

@pytest.mark.asyncio
async def test_handle_configuration_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de configuration"""
    error = ConfigurationError("Test config error")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "configuration" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_database_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de base de données"""
    error = DatabaseError("Test database error")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "base de données" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_discord_error(error_handler, mock_ctx):
    """Test la gestion des erreurs Discord"""
    original_error = Exception("API Error")
    error = DiscordError("Test Discord error", original_error)
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "discord" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_command_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de commande"""
    error = CommandError("test", "Invalid arguments")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "test" in error.message

@pytest.mark.asyncio
async def test_handle_resource_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de ressource"""
    error = ResourceError("test.png", "File not found")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "ressource" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_api_error(error_handler, mock_ctx):
    """Test la gestion des erreurs d'API"""
    error = APIError("Twitch", "/users", 404)
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "twitch" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_validation_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de validation"""
    error = ValidationError("username", "test", "Too short")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert error.message in mock_ctx.send.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_permission_error(error_handler, mock_ctx):
    """Test la gestion des erreurs de permission"""
    error = PermissionError(123, "MANAGE_MESSAGES")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "permission" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_handle_unknown_error(error_handler, mock_ctx):
    """Test la gestion des erreurs inconnues"""
    error = Exception("Unknown error")
    await error_handler.handle_error(error, mock_ctx)
    mock_ctx.send.assert_called_once()
    assert "inattendue" in mock_ctx.send.call_args[0][0].lower()

@pytest.mark.asyncio
async def test_custom_error_handler(error_handler, mock_ctx):
    """Test l'ajout d'un gestionnaire personnalisé"""
    custom_handler = AsyncMock()
    error_handler.register_handler(ValueError, custom_handler)
    
    error = ValueError("Test error")
    await error_handler.handle_error(error, mock_ctx)
    custom_handler.assert_called_once_with(error, mock_ctx)

@pytest.mark.asyncio
async def test_error_handler_without_context(error_handler):
    """Test la gestion des erreurs sans contexte Discord"""
    error = ConfigurationError("Test error")
    await error_handler.handle_error(error)  # Ne devrait pas lever d'exception 