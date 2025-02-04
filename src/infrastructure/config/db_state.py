import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.config import load_config
from src.infrastructure.config.database import init_db, async_session

logger = logging.getLogger(__name__)

class DatabaseState:
    """
    Gestionnaire d'état de la base de données implémentant le pattern Singleton.
    
    Cette classe assure qu'une seule instance de la connexion à la base de données
    est maintenue tout au long de l'exécution de l'application. Elle gère l'initialisation
    de la connexion et fournit un accès centralisé à la session de base de données.
    
    Attributes:
        _instance (Optional[DatabaseState]): Instance unique de la classe
        _initialized (bool): État d'initialisation de la base de données
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseState, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    async def ensure_initialized(cls):
        """
        Assure que la base de données est initialisée.
        
        Initialise la connexion si ce n'est pas déjà fait.
        
        Raises:
            RuntimeError: Si l'initialisation échoue
        """
        if not cls._initialized:
            try:
                config = load_config()
                await init_db(config.database)
                cls._initialized = True
                logger.info("Base de données initialisée avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
                raise
    
    @classmethod
    def get_session(cls) -> AsyncSession:
        if not cls._initialized or not async_session:
            raise RuntimeError("La base de données n'est pas initialisée")
        return async_session() 