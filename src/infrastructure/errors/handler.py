"""
Gestionnaire d'erreurs centralisé pour le bot Discord
"""
import logging
import sys
import traceback
from typing import Optional, Callable, Any, Type
from discord.ext import commands
from .exceptions import (
    BotError, ConfigurationError, DatabaseError,
    DiscordError, CommandError, ResourceError,
    APIError, ValidationError, PermissionError
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Gestionnaire d'erreurs centralisé"""
    
    def __init__(self):
        self._error_handlers = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Configure les gestionnaires d'erreurs par défaut"""
        self.register_handler(ConfigurationError, self._handle_config_error)
        self.register_handler(DatabaseError, self._handle_database_error)
        self.register_handler(DiscordError, self._handle_discord_error)
        self.register_handler(CommandError, self._handle_command_error)
        self.register_handler(ResourceError, self._handle_resource_error)
        self.register_handler(APIError, self._handle_api_error)
        self.register_handler(ValidationError, self._handle_validation_error)
        self.register_handler(PermissionError, self._handle_permission_error)
    
    def register_handler(self, error_type: Type[Exception], handler: Callable):
        """Enregistre un gestionnaire pour un type d'erreur spécifique"""
        self._error_handlers[error_type] = handler
    
    async def handle_error(self, error: Exception, ctx: Optional[commands.Context] = None) -> None:
        """Gère une erreur en utilisant le gestionnaire approprié"""
        error_type = type(error)
        
        # Chercher le gestionnaire le plus spécifique
        handler = None
        for error_class in error_type.__mro__:
            if error_class in self._error_handlers:
                handler = self._error_handlers[error_class]
                break
        
        if handler:
            try:
                await handler(error, ctx)
            except Exception as e:
                logger.error(f"Erreur dans le gestionnaire d'erreurs: {str(e)}")
                await self._handle_internal_error(e, ctx)
        else:
            await self._handle_unknown_error(error, ctx)
    
    async def _handle_config_error(self, error: ConfigurationError, ctx: Optional[commands.Context]):
        """Gère les erreurs de configuration"""
        logger.error(f"Erreur de configuration: {error.message}")
        if ctx:
            await ctx.send("❌ Une erreur de configuration est survenue. Contactez un administrateur.")
    
    async def _handle_database_error(self, error: DatabaseError, ctx: Optional[commands.Context]):
        """Gère les erreurs de base de données"""
        logger.error(f"Erreur de base de données: {error.message}")
        if ctx:
            await ctx.send("❌ Une erreur de base de données est survenue. Réessayez plus tard.")
    
    async def _handle_discord_error(self, error: DiscordError, ctx: Optional[commands.Context]):
        """Gère les erreurs liées à Discord"""
        logger.error(f"Erreur Discord: {error.message}")
        if error.discord_error:
            logger.error(f"Erreur originale: {str(error.discord_error)}")
        if ctx:
            await ctx.send("❌ Une erreur est survenue lors de l'interaction avec Discord.")
    
    async def _handle_command_error(self, error: CommandError, ctx: Optional[commands.Context]):
        """Gère les erreurs de commande"""
        logger.error(f"Erreur de commande: {error.message}")
        if ctx:
            await ctx.send(f"❌ {error.message}")
    
    async def _handle_resource_error(self, error: ResourceError, ctx: Optional[commands.Context]):
        """Gère les erreurs de ressources"""
        logger.error(f"Erreur de ressource: {error.message}")
        if ctx:
            await ctx.send("❌ Une ressource requise est manquante ou inaccessible.")
    
    async def _handle_api_error(self, error: APIError, ctx: Optional[commands.Context]):
        """Gère les erreurs d'API"""
        logger.error(f"Erreur API: {error.message}")
        if error.status_code:
            logger.error(f"Status code: {error.status_code}")
        if ctx:
            await ctx.send(f"❌ Une erreur est survenue lors de l'appel à {error.api_name}.")
    
    async def _handle_validation_error(self, error: ValidationError, ctx: Optional[commands.Context]):
        """Gère les erreurs de validation"""
        logger.error(f"Erreur de validation: {error.message}")
        if ctx:
            await ctx.send(f"❌ {error.message}")
    
    async def _handle_permission_error(self, error: PermissionError, ctx: Optional[commands.Context]):
        """Gère les erreurs de permission"""
        logger.error(f"Erreur de permission: {error.message}")
        if ctx:
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour cette action.")
    
    async def _handle_unknown_error(self, error: Exception, ctx: Optional[commands.Context]):
        """Gère les erreurs inconnues"""
        logger.error(f"Erreur inconnue: {str(error)}")
        logger.error("".join(traceback.format_exception(type(error), error, error.__traceback__)))
        if ctx:
            await ctx.send("❌ Une erreur inattendue est survenue.")
    
    async def _handle_internal_error(self, error: Exception, ctx: Optional[commands.Context]):
        """Gère les erreurs internes du gestionnaire d'erreurs"""
        logger.critical(f"Erreur interne du gestionnaire: {str(error)}")
        logger.critical("".join(traceback.format_exception(type(error), error, error.__traceback__)))
        if ctx:
            await ctx.send("❌ Une erreur critique est survenue dans le système.") 