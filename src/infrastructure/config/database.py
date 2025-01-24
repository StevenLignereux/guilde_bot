import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from src.config.environment import load_environment

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger la configuration
config = load_environment()

# Créer l'URL de la base de données
DATABASE_URL = config['database_url']
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

try:
    # Créer le moteur de base de données
    engine = create_engine(DATABASE_URL, echo=True)
except SQLAlchemyError as e:
    print(f"❌ Erreur lors de la création du moteur de base de données : {str(e)}")
    raise

# Créer une classe de base pour les modèles
Base = declarative_base()

# Créer une classe de session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialise la base de données en créant toutes les tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables : {str(e)}")
        raise

def get_db():
    """Générateur de session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 