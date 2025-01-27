import pytest
import logging
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.infrastructure.logging.logger import CustomFormatter, setup_logging
from src.config.config import Config, Environment

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.env = Environment.DEVELOPMENT
    config.is_development = True
    config.is_testing = False
    config.is_production = False
    return config

@pytest.fixture
def temp_log_dir(tmp_path):
    """Crée un répertoire temporaire pour les logs"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

def test_custom_formatter_session_id():
    """Test que le formateur ajoute bien un session ID"""
    formatter = CustomFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    assert "[" in formatted and "]" in formatted
    assert "Test message" in formatted

def test_setup_logging_development(temp_log_dir):
    """Test la configuration du logging en développement"""
    with patch('src.infrastructure.logging.logger.LOG_DIR', temp_log_dir):
        # Act
        setup_logging(is_development=True)
        
        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 2
        
        # Vérifier que les fichiers sont créés
        log_file = temp_log_dir / "bot.log"
        error_file = temp_log_dir / "errors.log"
        assert log_file.exists()
        assert error_file.exists()

def test_setup_logging_production(temp_log_dir):
    """Test la configuration du logging en production"""
    with patch('src.infrastructure.logging.logger.LOG_DIR', temp_log_dir):
        # Act
        setup_logging(is_development=False)
        
        # Assert
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 2
        
        # Vérifier que les fichiers sont créés
        log_file = temp_log_dir / "bot.log"
        error_file = temp_log_dir / "errors.log"
        assert log_file.exists()
        assert error_file.exists()

def test_error_logging(temp_log_dir):
    """Test que les erreurs sont bien loggées"""
    with patch('src.infrastructure.logging.logger.LOG_DIR', temp_log_dir):
        # Arrange
        setup_logging(is_development=True)
        test_logger = logging.getLogger("test")
        error_message = "Test error message"
        
        # Act
        test_logger.error(error_message)
        
        # Attendre que le fichier soit écrit
        time.sleep(0.1)
        
        # Assert
        log_file = temp_log_dir / "bot.log"
        error_file = temp_log_dir / "errors.log"
        
        assert log_file.exists()
        assert error_file.exists()
        
        # Vérifier le contenu des fichiers
        log_content = log_file.read_text()
        assert error_message in log_content
        assert "[ERROR]" in log_content

@pytest.mark.timeout(5)
def test_log_rotation(temp_log_dir):
    """Test la rotation des fichiers de logs"""
    with patch('src.infrastructure.logging.logger.LOG_DIR', temp_log_dir):
        # Arrange
        setup_logging(is_development=True)
        test_logger = logging.getLogger("test")
        
        # Act - Écrire suffisamment de logs pour déclencher la rotation
        large_message = "x" * 1000000  # 1MB
        for _ in range(15):  # 15MB au total
            test_logger.info(large_message)
            time.sleep(0.1)  # Laisser le temps d'écrire
        
        # Assert
        log_files = list(temp_log_dir.glob("bot.log*"))
        assert len(log_files) > 1  # Au moins le fichier principal + 1 rotation 