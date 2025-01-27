import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import os
from src.config.config import Config, Environment
from src.config.exceptions import (
    EnvironmentVariableError,
    InvalidEnvironmentError,
    ResourceNotFoundError
)

def test_environment_from_string_valid():
    """Test la création d'un Environment à partir d'une chaîne valide"""
    assert Environment.from_string("development") == Environment.DEVELOPMENT
    assert Environment.from_string("production") == Environment.PRODUCTION
    assert Environment.from_string("testing") == Environment.TESTING

def test_environment_from_string_invalid():
    """Test qu'une chaîne invalide lève une exception"""
    with pytest.raises(InvalidEnvironmentError) as exc_info:
        Environment.from_string("invalid")
    assert "invalid" in str(exc_info.value)
    assert "development" in str(exc_info.value)
    assert "production" in str(exc_info.value)
    assert "testing" in str(exc_info.value)

@pytest.fixture
def mock_env_vars():
    """Fixture pour simuler les variables d'environnement"""
    env_vars = {
        'DATABASE_URL': 'postgresql://user:pass@localhost/db',
        'DISCORD_TOKEN': 'discord_token',
        'WELCOME_CHANNEL_ID': '123',
        'STREAM_CHANNEL_ID': '456',
        'NEWS_CHANNEL_ID': '789',
        'TWITCH_CLIENT_ID': 'twitch_client_id',
        'TWITCH_CLIENT_SECRET': 'twitch_client_secret',
        'TWITCH_USERNAME': 'twitch_username',
        'WELCOME_IMAGE_PATH': 'path/to/welcome.png',
        'FONT_PATH': 'path/to/font.ttf'
    }
    with patch.dict('os.environ', env_vars, clear=True):
        yield env_vars

def test_config_load_development(mock_env_vars):
    """Test le chargement de la configuration en développement"""
    config = Config("development")
    assert config.is_development
    assert not config.is_production
    assert not config.is_testing
    
    # Vérifier la configuration de la base de données
    assert config.database.url == mock_env_vars['DATABASE_URL']
    assert config.database.pool_size == 5  # Valeur par défaut
    
    # Vérifier la configuration Discord
    assert config.discord.token == mock_env_vars['DISCORD_TOKEN']
    assert config.discord.welcome_channel_id == 123
    assert config.discord.command_prefix == '/'  # Valeur par défaut

def test_config_load_production_with_missing_var():
    """Test qu'une variable manquante lève une exception"""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(EnvironmentVariableError):
            Config("production")

def test_config_resource_validation_in_production(mock_env_vars):
    """Test la validation des ressources en production"""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(ResourceNotFoundError) as exc_info:
            Config("production")
        expected_path = os.path.normpath(mock_env_vars['WELCOME_IMAGE_PATH'])
        assert expected_path in str(exc_info.value)

def test_config_resource_validation_in_development(mock_env_vars):
    """Test que la validation des ressources est ignorée en développement"""
    with patch('pathlib.Path.exists', return_value=False):
        config = Config("development")  # Ne devrait pas lever d'exception
        assert config.is_development

def test_config_optional_values(mock_env_vars):
    """Test les valeurs optionnelles de la configuration"""
    with patch.dict('os.environ', {**mock_env_vars, 'COMMAND_PREFIX': '!'}, clear=True):
        config = Config()
        assert config.discord.command_prefix == '!'

def test_config_database_url_fallback(mock_env_vars):
    """Test le fallback de DATABASE_URL vers Database_URL"""
    env_vars = mock_env_vars.copy()
    del env_vars['DATABASE_URL']
    env_vars['Database_URL'] = 'postgresql://fallback@localhost/db'
    
    with patch.dict('os.environ', env_vars, clear=True):
        config = Config()
        assert config.database.url == 'postgresql://fallback@localhost/db' 