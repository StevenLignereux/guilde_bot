"""
Classes de base pour les commandes du bot
"""
from typing import Optional, List, Callable, Any, Dict, Union
from discord.ext import commands
from discord import app_commands
import discord
from functools import wraps
from enum import Enum
from ..errors.exceptions import CommandError, PermissionError, ValidationError

class BucketType(Enum):
    """Types de bucket pour les cooldowns"""
    default = 0
    user = 1
    guild = 2
    channel = 3
    member = 4
    category = 5
    role = 6

class BaseCommand(commands.Cog):
    """Classe de base pour toutes les commandes"""
    
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
    """Groupe de commandes slash avec gestion d'erreur intégrée"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_handler = None
        self._validators: Dict[str, Dict[str, Any]] = {}
    
    def add_validator(self, command_name: str, param_name: str, validator: Any):
        """Ajoute un validateur pour un paramètre d'une commande"""
        if command_name not in self._validators:
            self._validators[command_name] = {}
        self._validators[command_name][param_name] = validator
    
    async def _validate_params(self, command_name: str, **kwargs):
        """Valide les paramètres d'une commande"""
        if command_name in self._validators:
            for param_name, validator in self._validators[command_name].items():
                if param_name in kwargs:
                    try:
                        kwargs[param_name] = validator.validate(kwargs[param_name])
                    except ValidationError as e:
                        raise CommandError(
                            command_name,
                            f"Paramètre invalide : {e}",
                            original_error=e
                        )
        return kwargs
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Gère les erreurs des commandes du groupe"""
        if self.error_handler:
            await self.error_handler(interaction, error)

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
    def cooldown(rate: int, per: float, bucket_type: BucketType = BucketType.user):
        """Ajoute un cooldown à la commande slash
        
        Args:
            rate (int): Nombre d'utilisations autorisées
            per (float): Période en secondes
            bucket_type (BucketType): Type de bucket pour le cooldown
        """
        def decorator(func: Callable):
            if not hasattr(func, "__slash_command_checks__"):
                func.__slash_command_checks__ = []
            
            async def cooldown_check(interaction: discord.Interaction) -> bool:
                # Créer une clé unique pour ce cooldown
                if bucket_type == BucketType.user:
                    key = f"{func.__name__}:user:{interaction.user.id}"
                elif bucket_type == BucketType.guild:
                    key = f"{func.__name__}:guild:{interaction.guild_id}"
                elif bucket_type == BucketType.channel:
                    key = f"{func.__name__}:channel:{interaction.channel_id}"
                elif bucket_type == BucketType.member:
                    key = f"{func.__name__}:member:{interaction.guild_id}:{interaction.user.id}"
                elif bucket_type == BucketType.category:
                    key = f"{func.__name__}:category:{interaction.channel.category_id if interaction.channel.category else 0}"
                elif bucket_type == BucketType.role:
                    key = f"{func.__name__}:role:{interaction.user.top_role.id if isinstance(interaction.user, discord.Member) else 0}"
                else:
                    key = f"{func.__name__}:default"
                
                # Vérifier si un cooldown est actif
                if hasattr(interaction.client, "_command_cooldowns"):
                    cooldowns = interaction.client._command_cooldowns
                else:
                    cooldowns = {}
                    setattr(interaction.client, "_command_cooldowns", cooldowns)
                
                current_time = interaction.created_at.timestamp()
                
                if key in cooldowns:
                    # Nettoyer les utilisations expirées
                    cooldowns[key] = [t for t in cooldowns[key] if t > current_time - per]
                    
                    # Vérifier si le nombre d'utilisations est dépassé
                    if len(cooldowns[key]) >= rate:
                        retry_after = per - (current_time - cooldowns[key][0])
                        raise CommandError(
                            func.__name__,
                            f"Cette commande est en cooldown. Réessayez dans {int(retry_after)} secondes."
                        )
                else:
                    cooldowns[key] = []
                
                # Ajouter l'utilisation actuelle
                cooldowns[key].append(current_time)
                return True
            
            func.__slash_command_checks__.append(cooldown_check)
            return func
        return decorator

def create_slash_command(name: str, description: str = None, checks: List[Callable] = None):
    """Crée une commande slash avec gestion d'erreur et vérifications"""
    def decorator(func: Callable):
        # Récupérer les cooldowns définis sur la fonction
        cooldown_checks = getattr(func, "__slash_command_checks__", [])
        all_checks = (checks or []) + cooldown_checks
        
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