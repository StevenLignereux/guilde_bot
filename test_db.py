import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import logging

# Configuration des logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_connection():
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL n'est pas définie")
        return
    
    logger.info(f"URL de la base de données : {db_url}")
    
    try:
        # Configuration de la connexion avec des timeouts plus longs
        conn = await asyncpg.connect(
            db_url,
            timeout=60,  # Timeout de connexion à 60 secondes
            command_timeout=30,  # Timeout des commandes à 30 secondes
            server_settings={
                'statement_timeout': '60000',  # 60 secondes
                'idle_in_transaction_session_timeout': '60000'
            }
        )
        
        logger.info("Connexion établie avec succès")
        
        # Test simple
        logger.info("Test d'une requête simple...")
        result = await conn.fetchval('SELECT 1')
        logger.info(f"Résultat du test : {result}")
        
        await conn.close()
        logger.info("Connexion fermée")
        
    except asyncpg.exceptions.PostgresConnectionError as e:
        logger.error(f"Erreur de connexion PostgreSQL : {str(e)}")
        logger.error(f"Détails de l'erreur : {e.__class__.__name__}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}")
        logger.error(f"Type d'erreur : {e.__class__.__name__}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 