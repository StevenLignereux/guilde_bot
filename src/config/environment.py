import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_environment():
    """
    Charge les variables d'environnement depuis le fichier .env ou les variables système
    """
    # Essayer de charger depuis le fichier .env
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        logger.info(f"Chargement des variables depuis {env_path}")
        load_dotenv(env_path)
        logger.info("Variables chargées depuis le fichier .env")
    else:
        logger.info(f"❌ Fichier .env non trouvé à : {env_path}")
        logger.info("Utilisation des variables d'environnement système")
    
    # Vérifier les variables requises
    required_vars = {
        'Database_URL': os.getenv('DATABASE_URL') or os.getenv('Database_URL'),  # Support des deux formats
        'DISCORD_TOKEN': os.getenv('DISCORD_TOKEN')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
    
    return {
        'Database_URL': required_vars['Database_URL'],
        'DISCORD_TOKEN': required_vars['DISCORD_TOKEN'],
        'WELCOME_CHANNEL_ID': os.getenv('WELCOME_CHANNEL_ID'),
        'STREAM_CHANNEL_ID': os.getenv('STREAM_CHANNEL_ID'),
        'NEWS_CHANNEL_ID': os.getenv('NEWS_CHANNEL_ID')
    }