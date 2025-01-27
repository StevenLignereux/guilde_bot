import logging
import logging.handlers
import sys
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime
from src.config.config import Config, Environment
import os
from logging.handlers import RotatingFileHandler

# Définir le répertoire des logs
LOG_DIR = Path(os.getenv('LOG_DIR', 'logs'))

class CustomFormatter(logging.Formatter):
    """Formateur personnalisé pour les logs avec couleurs et session ID"""
    
    COLORS = {
        logging.DEBUG: '\033[36m',    # Cyan
        logging.INFO: '\033[32m',     # Vert
        logging.WARNING: '\033[33m',   # Jaune
        logging.ERROR: '\033[31m',     # Rouge
        logging.CRITICAL: '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, include_session_id: bool = True):
        self.session_id = str(uuid.uuid4())[:8]
        self.include_session_id = include_session_id
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        # Ajouter le session_id si nécessaire
        if self.include_session_id:
            record.msg = f'[{self.session_id}] {record.msg}'
            
        # Ajouter la couleur si la sortie est un terminal
        if sys.stderr.isatty():
            color = self.COLORS.get(record.levelno, self.RESET)
            record.levelname = f'{color}{record.levelname}{self.RESET}'
            
        return super().format(record)

def setup_logging(is_development: bool = True) -> None:
    """
    Configure le système de logging.
    
    Args:
        is_development: True si en mode développement, False si en production
    """
    # Créer le répertoire des logs s'il n'existe pas
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configuration de base
    log_level = logging.DEBUG if is_development else logging.INFO
    log_format = '%(asctime)s [%(levelname)s] %(name)s - [%(correlation_id)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurer le formateur avec un ID de corrélation par défaut
    class CorrelationFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, 'correlation_id'):
                record.correlation_id = 'N/A'
            return super().format(record)
    
    formatter = CorrelationFormatter(log_format, date_format)
    
    # Configuration du handler de fichier
    file_handler = RotatingFileHandler(
        LOG_DIR / 'bot.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Configuration du handler de console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Désactiver la propagation des logs de discord
    logging.getLogger('discord').propagate = False
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    
    # Logger le démarrage
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configuré en mode %s (niveau: %s)",
        "développement" if is_development else "production",
        logging.getLevelName(log_level)
    )
    
    # Logger spécifique pour les erreurs critiques
    error_logger = logging.getLogger('errors')
    error_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR / 'errors.log',
        maxBytes=5_000_000,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomFormatter(include_session_id=True))
    error_logger.addHandler(error_handler)
    
    # Capture des exceptions non gérées
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        error_logger.critical("Exception non gérée:", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    # Log initial
    root_logger.info(f"Système de logging initialisé en mode {'développement' if is_development else 'production'}") 