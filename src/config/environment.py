from pathlib import Path
import os
from dotenv import load_dotenv

def load_environment():
    """Charge les variables d'environnement depuis le fichier .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print(f"❌ Fichier .env non trouvé à : {env_path.absolute()}")
        raise OSError("Fichier .env non trouvé")
        
    load_dotenv(env_path)
    print(f"Fichier .env chargé depuis : {env_path.absolute()}")
    
    # Vérifier la présence des variables requises
    database_url = os.environ.get('Database_URL')
    if not database_url:
        raise OSError("La variable Database_URL n'est pas définie")
    
    # Retourner les variables d'environnement
    return {
        'database_url': database_url,
        'TOKEN': os.getenv('TOKEN'),
        'CHANNEL_ID': os.getenv('CHANNEL_ID')
    } 