import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config.config import DatabaseConfig
from contextlib import asynccontextmanager
import asyncio

# Configuration du logging
logger = logging.getLogger(__name__)

# Créer une classe de base pour les modèles
Base = declarative_base()

# Variables globales pour le moteur et la session
engine = None
async_session = None

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
            
        # Convertir l'URL PostgreSQL standard en URL asyncpg
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+asyncpg://', 1)
            
        logger.info(f"URL convertie : {db_url}")
        
        # Créer le moteur avec des paramètres de connexion optimisés
        engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=True,
            connect_args={
                "command_timeout": 60,  # 60 secondes pour les commandes
                "timeout": 30,         # 30 secondes pour la connexion
                "server_settings": {
                    "statement_timeout": "60000",  # 60 secondes en millisecondes
                    "idle_in_transaction_session_timeout": "60000"
                }
            },
            pool_timeout=30,           # 30 secondes pour obtenir une connexion du pool
            pool_recycle=1800,         # Recycler les connexions après 30 minutes
            pool_use_lifo=True,        # Utiliser les connexions les plus récentes d'abord
        )
        
        # Créer la factory de sessions avec retry
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Tester la connexion avec retry
        retry_count = 3
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with engine.begin() as conn:
                    from sqlalchemy import text
                    await conn.execute(text("SELECT 1"))
                    logger.info("Test de connexion réussi")
                    break
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    logger.warning(f"Tentative {attempt + 1}/{retry_count} échouée, nouvelle tentative...")
                    await asyncio.sleep(2 ** attempt)  # Attente exponentielle
                else:
                    raise last_error
        
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