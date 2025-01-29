import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config.config import DatabaseConfig
from contextlib import asynccontextmanager
import asyncio
import asyncpg
from urllib.parse import urlparse

# Configuration du logging
logger = logging.getLogger(__name__)

# Créer une classe de base pour les modèles
Base = declarative_base()

# Variables globales pour le moteur et la session
engine = None
async_session = None

async def test_connection(db_url: str) -> bool:
    """
    Teste la connexion à la base de données avec asyncpg directement.
    Inclut un mécanisme de retry avec backoff exponentiel.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Parser l'URL pour extraire les composants
            parsed = urlparse(db_url)
            user = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')

            logger.info(f"Tentative {attempt + 1}/{max_retries} de connexion à {host}:{port}/{database}")
            
            # Tenter une connexion directe avec des timeouts plus longs
            conn = await asyncpg.connect(
                user=user,
                password=password,
                database=database,
                host=host,
                port=port,
                ssl='require',
                command_timeout=30,
                timeout=30
            )
            
            # Tester la connexion
            await conn.execute('SELECT 1')
            await conn.close()
            
            logger.info(f"Test de connexion réussi après {attempt + 1} tentative(s)")
            return True
            
        except Exception as e:
            logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée: {str(e)}")
            if attempt < max_retries - 1:
                # Backoff exponentiel entre les tentatives
                wait_time = 2 ** attempt
                logger.info(f"Attente de {wait_time} secondes avant la prochaine tentative...")
                await asyncio.sleep(wait_time)
                continue
            
    logger.error("Échec de toutes les tentatives de connexion")
    return False

async def init_db(config: DatabaseConfig) -> None:
    """
    Initialise la connexion à la base de données.
    """
    global engine, async_session
    
    try:
        # Récupérer l'URL de la base de données
        db_url = os.getenv('DATABASE_URL')
        logger.info(f"URL de la base de données : {db_url}")
        
        if not db_url:
            raise ValueError("DATABASE_URL n'est pas définie dans les variables d'environnement")
        
        # Tester d'abord la connexion avec asyncpg
        if not await test_connection(db_url):
            raise ConnectionError("Impossible de se connecter à la base de données")
            
        # Convertir l'URL PostgreSQL standard en URL asyncpg
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
            
        logger.info(f"URL convertie : {db_url}")
        
        # Créer le moteur avec une configuration minimale
        engine = create_async_engine(
            db_url,
            connect_args={"ssl": "require"},
            echo=True
        )
        
        # Créer la factory de sessions
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Base de données initialisée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise

@asynccontextmanager
async def get_db():
    """
    Retourne une session de base de données dans un contexte.
    La session est automatiquement fermée à la fin du contexte.
    """
    if not async_session:
        raise RuntimeError("La session de base de données n'est pas initialisée")
    
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

async def get_session() -> AsyncSession:
    """
    Retourne une nouvelle session de base de données.
    """
    if not async_session:
        raise RuntimeError("La session de base de données n'est pas initialisée")
    return async_session() 