"""
Groupe de commandes slash avec support des alias
"""
from typing import Optional, List, Dict, Any, Callable
from discord import app_commands
import discord
from .aliases import AliasManager
from ..errors.exceptions import CommandError, ValidationError

class AliasedSlashCommandGroup(app_commands.Group):
    """Groupe de commandes slash avec support des alias"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_handler = None
        self._validators: Dict[str, Dict[str, Any]] = {}
        self.alias_manager = AliasManager()
        self._commands: Dict[str, app_commands.Command] = {}
    
    def add_command(self, command: app_commands.Command, aliases: List[str] = None):
        """Ajoute une commande au groupe avec ses alias"""
        # Ajouter la commande principale
        super().add_command(command)
        self._commands[command.name] = command
        
        # Ajouter les alias
        if aliases:
            for alias in aliases:
                # Créer une nouvelle commande pour l'alias
                alias_cmd = app_commands.Command(
                    name=alias,
                    description=command.description,
                    callback=command.callback,
                    parent=self,
                    extras=command.extras
                )
                super().add_command(alias_cmd)
                self._commands[alias] = alias_cmd
                self.alias_manager.add_alias(command.name, alias)
    
    def get_command(self, name: str) -> Optional[app_commands.Command]:
        """Retourne une commande par son nom ou alias"""
        real_name = self.alias_manager.get_command_name(name)
        return self._commands.get(real_name)
    
    def track_command_usage(self, command_name: str):
        """Incrémente le compteur d'utilisation d'une commande"""
        self.alias_manager.track_usage(command_name)
    
    def get_command_usage(self, command_name: str) -> int:
        """Retourne le nombre d'utilisations d'une commande"""
        usage = self.alias_manager.get_usage(command_name)
        return usage.total_uses if usage else 0
    
    def get_command_aliases(self, command_name: str) -> List[str]:
        """Retourne la liste des alias d'une commande"""
        return self.alias_manager.get_aliases(command_name)
    
    async def _validate_params(self, command_name: str, **kwargs):
        """Valide les paramètres d'une commande"""
        real_name = self.alias_manager.get_command_name(command_name)
        if real_name in self._validators:
            for param_name, validator in self._validators[real_name].items():
                if param_name in kwargs:
                    try:
                        kwargs[param_name] = validator.validate(kwargs[param_name])
                    except ValidationError as e:
                        raise CommandError(
                            real_name,
                            f"Paramètre invalide : {e}",
                            original_error=e
                        )
        return kwargs
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Gère les erreurs des commandes du groupe"""
        if self.error_handler:
            await self.error_handler(interaction, error)

def create_aliased_command(name: str, description: str = None, aliases: List[str] = None, checks: List[Callable] = None):
    """Crée une commande slash avec support des alias
    
    Args:
        name (str): Nom de la commande
        description (str, optional): Description de la commande
        aliases (List[str], optional): Liste des alias de la commande
        checks (List[Callable], optional): Liste des vérifications à effectuer
    """
    def decorator(func: Callable):
        # Créer la commande principale
        command = app_commands.Command(
            name=name,
            description=description or func.__doc__ or "Aucune description",
            callback=func
        )
        
        # Ajouter les vérifications
        if checks:
            command.checks = checks
        
        # Stocker les alias pour les utiliser lors de l'ajout au groupe
        if aliases:
            command.__slash_command_aliases__ = aliases
        
        return command
    return decorator 