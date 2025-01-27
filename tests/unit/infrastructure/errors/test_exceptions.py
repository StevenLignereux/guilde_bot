import pytest
from src.infrastructure.errors.exceptions import (
    BotError, ConfigurationError, DatabaseError,
    DiscordError, CommandError, ResourceError,
    APIError, ValidationError, PermissionError
)

def test_bot_error_base():
    """Test l'exception de base"""
    error = BotError("Test message", {"detail": "value"})
    assert str(error) == "Test message"
    assert error.message == "Test message"
    assert error.details == {"detail": "value"}

def test_configuration_error():
    """Test l'exception de configuration"""
    error = ConfigurationError("Config invalide")
    assert isinstance(error, BotError)
    assert str(error) == "Config invalide"

def test_database_error():
    """Test l'exception de base de données"""
    error = DatabaseError("Erreur SQL")
    assert isinstance(error, BotError)
    assert str(error) == "Erreur SQL"

def test_discord_error():
    """Test l'exception Discord"""
    original_error = Exception("Discord API Error")
    error = DiscordError("Erreur Discord", original_error)
    assert isinstance(error, BotError)
    assert error.discord_error == original_error

def test_command_error():
    """Test l'exception de commande"""
    error = CommandError("test", "Arguments invalides")
    assert isinstance(error, BotError)
    assert error.command_name == "test"
    assert "test" in str(error)
    assert "Arguments invalides" in str(error)

def test_resource_error():
    """Test l'exception de ressource"""
    error = ResourceError("image.png", "Fichier non trouvé")
    assert isinstance(error, BotError)
    assert error.resource_path == "image.png"
    assert "image.png" in str(error)

def test_api_error():
    """Test l'exception d'API"""
    error = APIError("Twitch", "/users", 404, "Not Found")
    assert isinstance(error, BotError)
    assert error.api_name == "Twitch"
    assert error.endpoint == "/users"
    assert error.status_code == 404
    assert "Twitch" in str(error)
    assert "/users" in str(error)
    assert "404" in str(error)

def test_validation_error():
    """Test l'exception de validation"""
    error = ValidationError("username", "test", "Trop court")
    assert isinstance(error, BotError)
    assert error.field == "username"
    assert error.value == "test"
    assert "username" in str(error)
    assert "Trop court" in str(error)

def test_permission_error():
    """Test l'exception de permission"""
    error = PermissionError(user_id=123456, permission="MANAGE_MESSAGES", channel_id=789012)
    assert isinstance(error, BotError)
    assert error.user_id == 123456
    assert error.permission == "MANAGE_MESSAGES"
    assert error.channel_id == 789012
    assert str(error) == "L'utilisateur 123456 n'a pas la permission MANAGE_MESSAGES dans le canal 789012" 