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
        
        # Créer le moteur avec des paramètres de connexion plus stricts
        engine = create_async_engine(
            db_url,
            pool_pre_ping=True,  # Vérifie la connexion avant utilisation
            pool_size=5,
            max_overflow=10,
            echo=True  # Active les logs SQL
        )
        
        # Créer la factory de sessions
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Tester la connexion
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            logger.info("Test de connexion réussi")
        
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