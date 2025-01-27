import pytest
import logging
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

def test_custom_formatter():
    """Test le formateur personnalisé"""
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
    assert "Test message" in formatted

def test_setup_logging(mock_config, tmp_path):
    """Test la configuration basique du logging"""
    # Créer le dossier de logs dans le répertoire temporaire
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    # Patcher la création du dossier de logs pour utiliser notre dossier temporaire
    with patch('src.infrastructure.logging.logger.Path', return_value=log_dir):
        setup_logging(mock_config)
        logger = logging.getLogger()
        
        # Vérifier le niveau de log
        assert logger.level == logging.DEBUG
        
        # Vérifier les handlers
        assert len(logger.handlers) == 2
        
        # Écrire un message de test
        logger.info("Test message")
        
        # Attendre un peu pour s'assurer que le fichier est écrit
        import time
        time.sleep(0.1)
        
        # Vérifier que le fichier de log a été créé
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) >= 1
        
        # Vérifier le contenu du fichier
        log_content = log_files[0].read_text()
        assert "Test message" in log_content 