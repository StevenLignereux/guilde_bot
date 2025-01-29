from typing import Optional
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
import logging
from enum import Enum
from .exceptions import EnvironmentVariableError, InvalidEnvironmentError, ResourceNotFoundError

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    url: str = os.getenv('Database_URL', 'postgresql://postgres:postgres@localhost:5432/guilde_bot')
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30

    def __post_init__(self):
        if self.url and self.url.startswith("postgres://"):
            # Railway utilise postgres://, mais SQLAlchemy préfère postgresql://
            self.url = self.url.replace("postgres://", "postgresql://", 1)

@dataclass
class DiscordConfig:
    token: str
    welcome_channel_id: int
    stream_channel_id: int
    news_channel_id: int
    command_prefix: str = "/"

@dataclass
class TwitchConfig:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None

    @classmethod
    def create_from_env(cls) -> 'TwitchConfig':
        """Crée une configuration Twitch à partir des variables d'environnement"""
        try:
            client_id = os.getenv('TWITCH_CLIENT_ID')
            client_secret = os.getenv('TWITCH_CLIENT_SECRET')
            username = os.getenv('TWITCH_USERNAME')
            
            if all([client_id, client_secret, username]):
                return cls(
                    client_id=client_id,
                    client_secret=client_secret,
                    username=username
                )
            else:
                logger.warning("Configuration Twitch incomplète, les fonctionnalités Twitch seront désactivées")
                return cls()
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la configuration Twitch: {e}")
            return cls()

@dataclass
class ResourceConfig:
    welcome_image_path: Path
    font_path: Path

    @classmethod
    def create_from_env(cls) -> 'ResourceConfig':
        """Crée une configuration des ressources avec des chemins par défaut"""
        # Chemins par défaut relatifs au dossier du projet
        default_welcome_path = Path("src/resources/images/welcome.png")
        default_font_path = Path("src/resources/fonts/default.ttf")
        
        # Utiliser les variables d'environnement si définies, sinon utiliser les chemins par défaut
        welcome_path = os.getenv('WELCOME_IMAGE_PATH')
        font_path = os.getenv('FONT_PATH')
        
        return cls(
            welcome_image_path=Path(welcome_path) if welcome_path else default_welcome_path,
            font_path=Path(font_path) if font_path else default_font_path
        )

    def validate(self):
        """Vérifie que les ressources existent"""
        if not self.welcome_image_path.exists():
            raise ResourceNotFoundError(
                f"L'image de bienvenue n'existe pas: {self.welcome_image_path}\n"
                f"Veuillez placer une image 'welcome.png' dans le dossier {self.welcome_image_path.parent}"
            )
        if not self.font_path.exists():
            raise ResourceNotFoundError(
                f"La police n'existe pas: {self.font_path}\n"
                f"Veuillez placer une police 'default.ttf' dans le dossier {self.font_path.parent}"
            )

class Config:
    def __init__(self, env: Optional[str] = None):
        self.env = Environment.from_string(env.lower() if env else "development")
        self._load_environment()
        # Charger la base de données en premier
        self.database = self._load_database_config()
        self.twitch = self._load_twitch_config()
        self.resources = self._load_resource_config()
        self.discord = self._load_discord_config()
        
        # Valider les ressources en production
        if self.is_production:
            self.resources.validate()

    def _load_environment(self) -> None:
        """Charge les variables d'environnement depuis le fichier .env"""
        env_path = Path(".env")
        if env_path.exists():
            logger.info(f"Chargement des variables depuis {env_path}")
            load_dotenv(env_path)
            logger.info("Variables chargées depuis le fichier .env")
        else:
            logger.info("Utilisation des variables d'environnement système")

    def _get_required_env(self, key: str) -> str:
        """
        Récupère une variable d'environnement requise.
        
        Args:
            key: Le nom de la variable d'environnement à récupérer.
            
        Returns:
            str: La valeur de la variable d'environnement.
            
        Raises:
            EnvironmentVariableError: Si la variable d'environnement n'est pas définie.
        """
        value = os.getenv(key)
        if value is None:
            raise EnvironmentVariableError(f"La variable d'environnement {key} est requise mais n'est pas définie")
        return value

    def _get_optional_env(self, key: str, default: str = '') -> str:
        """Récupère une variable d'environnement optionnelle"""
        return os.getenv(key, default)

    def _load_database_config(self) -> DatabaseConfig:
        """Charge la configuration de la base de données"""
        return DatabaseConfig(
            pool_size=int(self._get_optional_env('DATABASE_POOL_SIZE', '5')),
            max_overflow=int(self._get_optional_env('DATABASE_MAX_OVERFLOW', '10')),
            pool_timeout=int(self._get_optional_env('DATABASE_POOL_TIMEOUT', '30'))
        )

    def _load_discord_config(self) -> DiscordConfig:
        """Charge la configuration Discord"""
        token = self._get_required_env('DISCORD_TOKEN')
        welcome_channel_id = int(self._get_required_env('WELCOME_CHANNEL_ID'))
        stream_channel_id = int(self._get_required_env('STREAM_CHANNEL_ID'))
        news_channel_id = int(self._get_required_env('NEWS_CHANNEL_ID'))
        command_prefix = self._get_optional_env('COMMAND_PREFIX', '/')
        
        if not command_prefix:
            command_prefix = '/'
        
        return DiscordConfig(
            token=token,
            welcome_channel_id=welcome_channel_id,
            stream_channel_id=stream_channel_id,
            news_channel_id=news_channel_id,
            command_prefix=command_prefix
        )

    def _load_twitch_config(self) -> TwitchConfig:
        """Charge la configuration Twitch"""
        return TwitchConfig.create_from_env()

    def _load_resource_config(self) -> ResourceConfig:
        """Charge la configuration des ressources"""
        return ResourceConfig.create_from_env()

    @property
    def is_production(self) -> bool:
        return self.env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.env == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.env == Environment.TESTING 

def load_config() -> Config:
    """
    Charge la configuration depuis les variables d'environnement
    """
    try:
        logger.info("Chargement des variables depuis .env")
        return Config()
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {e}")
        raise

class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

    @classmethod
    def from_string(cls, env: str) -> 'Environment':
        try:
            return cls(env.lower())
        except ValueError:
            raise InvalidEnvironmentError(env, [e.value for e in cls]) 