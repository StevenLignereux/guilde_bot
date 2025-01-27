import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config.config import DatabaseConfig
from contextlib import asynccontextmanager

# Configuration du logging
logger = logging.getLogger(__name__)

# Créer une classe de base pour les modèles
Base = declarative_base()

# Variables globales pour le moteur et la session
engine = None
async_session = None
DATABASE_URL = os.getenv('Database_URL', 'postgresql://postgres:postgres@localhost:5432/guilde_bot')

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

def get_test_session() -> AsyncSession:
    """
    Retourne une session de test.
    À utiliser uniquement dans les tests.
    """
    if not async_session:
        raise RuntimeError("La session de base de données n'est pas initialisée")
    return async_session()

async def init_db(config: DatabaseConfig) -> None:
    """
    Initialise la connexion à la base de données.
    """
    global engine, async_session
    
    try:
        # Convertir l'URL PostgreSQL standard en URL asyncpg si nécessaire
        db_url = DATABASE_URL
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        # Créer le moteur
        engine = create_async_engine(db_url)
        
        # Créer la factory de sessions
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Base de données initialisée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise

async def get_session() -> AsyncSession:
    """
    Retourne une nouvelle session de base de données.
    """
    if not async_session:
        raise RuntimeError("La session de base de données n'est pas initialisée")
    return async_session() 