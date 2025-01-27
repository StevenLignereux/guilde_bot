"""
Exceptions personnalisées pour le bot Discord
"""
from typing import Optional, Any

class BotError(Exception):
    """Classe de base pour toutes les erreurs du bot"""
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ConfigurationError(BotError):
    """Erreurs liées à la configuration"""
    pass

class DatabaseError(BotError):
    """Erreurs liées à la base de données"""
    pass

class DiscordError(BotError):
    """Erreurs liées à l'API Discord"""
    def __init__(self, message: str, discord_error: Optional[Exception] = None):
        super().__init__(message, discord_error)
        self.discord_error = discord_error

class CommandError(BotError):
    """Erreurs liées aux commandes"""
    def __init__(self, command_name: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"Erreur dans la commande '{command_name}': {message}", original_error)
        self.command_name = command_name

class ResourceError(BotError):
    """Erreurs liées aux ressources (images, fichiers, etc.)"""
    def __init__(self, resource_path: str, message: str):
        super().__init__(f"Erreur avec la ressource '{resource_path}': {message}")
        self.resource_path = resource_path

class APIError(BotError):
    """Erreurs liées aux appels API externes (Twitch, etc.)"""
    def __init__(self, api_name: str, endpoint: str, status_code: Optional[int] = None, response: Optional[str] = None):
        message = f"Erreur lors de l'appel à l'API {api_name} (endpoint: {endpoint})"
        if status_code:
            message += f" - Status: {status_code}"
        super().__init__(message, {"response": response})
        self.api_name = api_name
        self.endpoint = endpoint
        self.status_code = status_code

class ValidationError(BotError):
    """Erreurs de validation des données"""
    def __init__(self, field: str, value: Any, message: str):
        super().__init__(f"Erreur de validation pour '{field}': {message}")
        self.field = field
        self.value = value

class PermissionError(BotError):
    """Exception levée quand un utilisateur n'a pas la permission requise"""
    def __init__(self, user_id: int, permission: str, channel_id: int, message: str = None):
        self.user_id = user_id
        self.permission = permission
        self.channel_id = channel_id
        if not message:
            message = f"L'utilisateur {user_id} n'a pas la permission {permission} dans le canal {channel_id}"
        super().__init__(message)

    def __str__(self) -> str:
        return self.message 