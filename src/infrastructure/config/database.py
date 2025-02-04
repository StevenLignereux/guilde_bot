import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.config import DatabaseConfig
from contextlib import asynccontextmanager
import asyncio
import asyncpg
from urllib.parse import urlparse
from typing import Optional

# Créer la classe Base pour les modèles SQLAlchemy
Base = declarative_base()

# Configuration du logging
logger = logging.getLogger(__name__)

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

async def init_db(config):
    """Initialise la connexion à la base de données."""
    try:
        # Construire l'URL de connexion à partir de la config
        if not hasattr(config, 'url'):
            raise ValueError("La configuration de la base de données est invalide")
            
        database_url = config.url
        if not database_url:
            raise ValueError("L'URL de la base de données est vide")
            
        # Ajouter le préfixe async si nécessaire
        if not database_url.startswith('postgresql+asyncpg://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            
        logger.info(f"URL de la base de données : {database_url}")
        
        # Créer le moteur
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        
        # Créer les tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Créer la session factory
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Base de données initialisée avec succès")
        return engine, async_session
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise

@asynccontextmanager
async def get_db():
    """
    Gestionnaire de contexte pour obtenir une session de base de données.
    
    Yield:
        AsyncSession: Session de base de données active
        
    Example:
        async with get_db() as session:
            result = await session.execute(query)
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