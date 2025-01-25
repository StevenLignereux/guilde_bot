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
    database_url = os.getenv('DATABASE_URL') or os.getenv('Database_URL')  # Support des deux formats
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not database_url:
        raise ValueError("La variable DATABASE_URL ou Database_URL est requise")
    if not discord_token:
        raise ValueError("La variable DISCORD_TOKEN est requise")
    
    return {
        'database_url': database_url,  # Utilisation de la clé en minuscules
        'DISCORD_TOKEN': discord_token,
        'WELCOME_CHANNEL_ID': os.getenv('WELCOME_CHANNEL_ID'),
        'STREAM_CHANNEL_ID': os.getenv('STREAM_CHANNEL_ID'),
        'NEWS_CHANNEL_ID': os.getenv('NEWS_CHANNEL_ID')
    }