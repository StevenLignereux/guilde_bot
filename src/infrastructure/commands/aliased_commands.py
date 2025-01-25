"""
Commandes slash avec support des alias
"""
from typing import List, Callable, Dict, Any
from discord import app_commands
import discord
from functools import wraps
from .aliases import AliasManager
from ..errors.exceptions import CommandError, PermissionError

class AliasedCommand(app_commands.Command):
    """Commande slash avec support des alias"""
    
    def __init__(self, name: str, callback: Callable, description: str = None, aliases: List[str] = None, **kwargs):
        super().__init__(
            name=name,
            description=description or callback.__doc__ or "Aucune description",
            callback=callback,
            **kwargs
        )
        self.aliases = aliases or []
        self.alias_manager = AliasManager()
        
        # Enregistrer les alias
        for alias in self.aliases:
            self.alias_manager.add_alias(name, alias)
    
    async def _invoke(self, interaction: discord.Interaction, *args, **kwargs):
        """Invoque la commande et suit son utilisation"""
        try:
            # Suivre l'utilisation
            self.alias_manager.track_usage(interaction.command.name)
            
            # Exécuter la commande
            return await super()._invoke(interaction, *args, **kwargs)
        except Exception as e:
            if not isinstance(e, (CommandError, PermissionError)):
                e = CommandError(
                    self.name,
                    str(e),
                    original_error=e
                )
            raise e

def create_aliased_command(name: str, description: str = None, aliases: List[str] = None, checks: List[Callable] = None):
    """Crée une commande slash avec support des alias
    
    Args:
        name (str): Nom de la commande
        description (str, optional): Description de la commande
        aliases (List[str], optional): Liste des alias de la commande
        checks (List[Callable], optional): Liste des vérifications à effectuer
    """
    def decorator(func: Callable):
        # Créer la commande avec ses alias
        command = AliasedCommand(
            name=name,
            callback=func,
            description=description,
            aliases=aliases
        )
        
        # Ajouter les vérifications
        if checks:
            command.checks = checks
        
        return command
    return decorator 