"""
Classes de base pour les commandes du bot
"""
from typing import Optional, List, Callable, Any, Dict, Union, Awaitable
from discord.ext import commands
from discord import app_commands
import discord
from functools import wraps
from enum import Enum
from ..errors.exceptions import CommandError, PermissionError, ValidationError
from .aliases import AliasManager
import asyncio
from discord.app_commands import CommandOnCooldown
from discord.enums import AppCommandOptionType

class BucketType(Enum):
    """Types de bucket pour la gestion des cooldowns des commandes.
    
    Cette énumération définit les différents types de bucket utilisés pour gérer
    les limites de taux d'utilisation (cooldowns) des commandes. Chaque type détermine
    comment les cooldowns sont appliqués et partagés entre les utilisateurs.
    
    Attributes:
        default (int): Cooldown global pour toutes les utilisations de la commande
        user (int): Cooldown par utilisateur
        guild (int): Cooldown par serveur
        channel (int): Cooldown par canal
        member (int): Cooldown par membre dans un serveur spécifique
        category (int): Cooldown par catégorie de canal
        role (int): Cooldown par rôle
    """

class BaseCommand(commands.Cog):
    """
    Classe de base pour toutes les commandes du bot.
    
    Fournit les fonctionnalités communes à toutes les commandes :
    gestion des alias, validation des paramètres, gestion des erreurs.
    
    Attributes:
        alias_manager (AliasManager): Gestionnaire des alias de commandes
        _validators (Dict): Dictionnaire des validateurs par commande
        error_handler (Callable): Gestionnaire d'erreurs personnalisé
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._setup_help()
    
    def _setup_help(self):
        """Configure l'aide pour les commandes du cog"""
        if not self.__doc__:
            self.__doc__ = "Aucune description disponible"
        
        # Ajouter la description des commandes à la documentation
        commands_help = []
        for cmd in self.get_commands():
            if not cmd.hidden:
                cmd_help = f"• /{cmd.name}"
                if cmd.help:
                    cmd_help += f" - {cmd.help}"
                commands_help.append(cmd_help)
        
        if commands_help:
            self.__doc__ += "\n\nCommandes disponibles:\n" + "\n".join(commands_help)
    
    def get_commands(self) -> List[commands.Command]:
        """Retourne la liste des commandes du cog"""
        return [cmd for cmd in self.walk_commands()]

    def validate_params(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Valide les paramètres d'une commande.
        
        Args:
            command_name (str): Nom de la commande
            **kwargs: Paramètres à valider
            
        Returns:
            Dict[str, Any]: Paramètres validés
            
        Raises:
            CommandError: Si la validation échoue
        """
        # Validation logic here
        return kwargs  # Retourne les paramètres, validés ou non

class CommandCheck:
    """Classe utilitaire pour les vérifications de commandes"""
    
    @staticmethod
    def has_permission(permission: str):
        """Vérifie si l'utilisateur a la permission requise"""
        async def predicate(ctx: commands.Context):
            if not isinstance(ctx.author, discord.Member):
                return False
            
            perms = ctx.channel.permissions_for(ctx.author)
            if not getattr(perms, permission, False):
                raise PermissionError(
                    ctx.author.id,
                    permission,
                    ctx.channel.id
                )
            return True
        return commands.check(predicate)
    
    @staticmethod
    def cooldown(rate: int, per: float, type: commands.BucketType = commands.BucketType.user):
        """Ajoute un cooldown à la commande"""
        return commands.cooldown(rate, per, type)
    
    @staticmethod
    def guild_only():
        """Restreint la commande aux serveurs"""
        return commands.guild_only()

def command_error_handler(func: Callable) -> Callable:
    """Décorateur pour gérer les erreurs de commande"""
    @wraps(func)
    async def wrapper(self, ctx: commands.Context, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            if not isinstance(e, CommandError):
                e = CommandError(
                    ctx.command.name if ctx.command else "unknown",
                    str(e),
                    original_error=e
                )
            await self.bot.error_handler.handle_error(e, ctx)
    return wrapper

class SlashCommandGroup(app_commands.Group):
    """Groupe de commandes slash avec gestion des alias et du suivi d'utilisation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._aliases = {}  # {alias: command_name}
        self._command_usage = {}  # {command_name: count}
        self._validators = {}  # {command_name: {param_name: validator}}
        self.error_handler = None
        self.alias_manager = AliasManager()
    
    def add_validator(self, command_name: str, param_name: str, validator: Any):
        """Ajoute un validateur pour un paramètre d'une commande"""
        if command_name not in self._validators:
            self._validators[command_name] = {}
        self._validators[command_name][param_name] = validator
    
    def add_command(self, command: app_commands.Command, aliases: List[str] = []):
        """
        Ajoute une commande au groupe avec ses alias
        
        Args:
            command (app_commands.Command): La commande à ajouter
            aliases (List[str]): Liste des alias de la commande
        """
        super().add_command(command)
        
        if aliases:
            for alias in aliases:
                if alias in self._aliases:
                    raise ValueError(f"L'alias '{alias}' est déjà utilisé")
                self._aliases[alias] = command.name
                
        if command.name not in self._command_usage:
            self._command_usage[command.name] = 0
        
        if aliases:
            for alias in aliases:
                # Créer une copie de la commande avec un nom différent
                alias_command = app_commands.Command(
                    name=alias,
                    description=command.description,
                    callback=command.callback,
                    parent=self,
                    extras=command.extras
                )
                super().add_command(alias_command)
                self.alias_manager.add_alias(command.name, alias)
    
    def get_command_name(self, alias: str) -> Optional[str]:
        """Retourne le nom de la commande associée à l'alias"""
        return self._aliases.get(alias)
    
    def track_command_usage(self, command_name: str):
        """Incrémente le compteur d'utilisation d'une commande"""
        if command_name in self._command_usage:
            self._command_usage[command_name] += 1
        
        self.alias_manager.track_usage(command_name)
    
    def get_command_usage(self, command_name: str) -> int:
        """Retourne le nombre d'utilisations d'une commande"""
        return self._command_usage.get(command_name, 0)
    
    def get_command_aliases(self, command_name: str) -> List[str]:
        """Retourne la liste des alias d'une commande"""
        return [alias for alias, cmd in self._aliases.items() if cmd == command_name]
    
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
            if asyncio.iscoroutinefunction(self.error_handler):
                await self.error_handler(interaction, error)
            else:
                self.error_handler(interaction, error)
                await interaction.response.send_message("Une erreur est survenue.", ephemeral=True)

class SlashCommandCheck:
    """Classe utilitaire pour les vérifications des commandes slash"""
    
    @staticmethod
    def has_permission(permission: str):
        """Vérifie si l'utilisateur a la permission requise"""
        async def check(interaction: discord.Interaction) -> bool:
            if not isinstance(interaction.user, discord.Member):
                return False
            
            perms = interaction.channel.permissions_for(interaction.user)
            if not getattr(perms, permission, False):
                raise PermissionError(
                    interaction.user.id,
                    permission,
                    interaction.channel_id
                )
            return True
        return check
    
    @staticmethod
    def has_role(role_id: Union[int, str]):
        """Vérifie si l'utilisateur a le rôle requis"""
        async def check(interaction: discord.Interaction) -> bool:
            if not isinstance(interaction.user, discord.Member):
                return False
            
            role = discord.utils.get(interaction.guild.roles, id=int(role_id))
            if not role or role not in interaction.user.roles:
                raise PermissionError(
                    interaction.user.id,
                    f"role_{role_id}",
                    interaction.channel_id,
                    "Vous n'avez pas le rôle requis pour utiliser cette commande"
                )
            return True
        return check
    
    @staticmethod
    def is_owner():
        """Vérifie si l'utilisateur est le propriétaire du bot"""
        async def check(interaction: discord.Interaction) -> bool:
            app = interaction.client.application
            if not app or interaction.user.id != app.owner.id:
                raise PermissionError(
                    interaction.user.id,
                    "owner",
                    interaction.channel_id,
                    "Seul le propriétaire du bot peut utiliser cette commande"
                )
            return True
        return check
    
    @staticmethod
    def cooldown(rate: int, per: float, bucket_type: Optional[str] = "user"):
        """
        Un décorateur pour ajouter un cooldown à une commande slash
        
        Args:
            rate (int): Nombre d'utilisations
            per (float): Période en secondes
            bucket_type (str): Type de bucket ("user", "channel", "guild")
        """
        def decorator(func: Callable) -> Callable:
            # ... rest of the cooldown implementation ...
            pass
        return decorator

def create_slash_command(name: str, description: str = None, aliases: List[str] = None, checks: List[Callable] = None):
    """Crée une commande slash avec gestion d'erreur et vérifications
    
    Args:
        name (str): Nom de la commande
        description (str, optional): Description de la commande
        aliases (List[str], optional): Liste des alias de la commande
        checks (List[Callable], optional): Liste des vérifications à effectuer
    """
    def decorator(func: Callable):
        # Récupérer les cooldowns définis sur la fonction
        cooldown_checks = getattr(func, "__slash_command_checks__", [])
        all_checks = (checks or []) + cooldown_checks
        
        # Créer la commande principale
        @app_commands.command(name=name, description=description or func.__doc__ or "Aucune description")
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            try:
                # Exécuter les vérifications
                if all_checks:
                    for check in all_checks:
                        result = await check(interaction)
                        if not result:
                            return
                
                # Suivre l'utilisation de la commande si dans un groupe
                if isinstance(self, SlashCommandGroup):
                    self.track_command_usage(interaction.command.name)
                
                return await func(self, interaction, *args, **kwargs)
            except PermissionError as e:
                raise e
            except Exception as e:
                if not isinstance(e, CommandError):
                    e = CommandError(
                        name,
                        str(e),
                        original_error=e
                    )
                raise e
        
        # Stocker les alias pour les utiliser lors de l'ajout au groupe
        if aliases:
            wrapper.__slash_command_aliases__ = aliases
        
        return wrapper
    return decorator

def create_subcommand(group: SlashCommandGroup, name: str, description: str = None, checks: List[Callable] = None, **validators):
    """Crée une sous-commande slash avec validation des paramètres et vérifications"""
    def decorator(func: Callable):
        async def command_callback(self, interaction: discord.Interaction, *args, **kwargs):
            try:
                # Exécuter les vérifications
                if checks:
                    for check in checks:
                        if not await check(interaction):
                            return
                
                # Valider les paramètres
                kwargs = await group._validate_params(name, **kwargs)
                return await func(self, interaction, *args, **kwargs)
            except Exception as e:
                if not isinstance(e, CommandError):
                    e = CommandError(
                        name,
                        str(e),
                        original_error=e
                    )
                await self.bot.error_handler.handle_error(e, interaction)
        
        # Copier les métadonnées de la fonction originale
        command_callback.__name__ = func.__name__
        command_callback.__doc__ = func.__doc__
        
        # Créer la commande
        command = app_commands.Command(
            name=name,
            description=description or func.__doc__ or "Aucune description",
            callback=command_callback,
            parent=group,
            auto_locale_strings=True,
            extras={"validators": validators, "checks": checks}
        )
        
        # Enregistrer les validateurs
        for param_name, validator in validators.items():
            group.add_validator(name, param_name, validator)
        
        # Ajouter la commande au groupe
        group.add_command(command)
        
        return command
    return decorator

class AliasedSlashCommandGroup(app_commands.Group):
    """Groupe de commandes slash avec support des alias"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_handler: Optional[Callable[[discord.Interaction, Exception], Awaitable[None] | None]] = None
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