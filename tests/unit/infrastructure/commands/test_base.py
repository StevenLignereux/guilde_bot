import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands
import discord
from discord import app_commands
from src.infrastructure.commands.base import (
    BaseCommand, CommandCheck, command_error_handler,
    SlashCommandGroup, create_slash_command, create_subcommand,
    SlashCommandCheck, BucketType
)
from src.infrastructure.commands.validators import StringValidator, NumberValidator
from src.infrastructure.errors.exceptions import PermissionError, CommandError

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.error_handler = MagicMock()
    bot.error_handler.handle_error = AsyncMock()
    return bot

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=commands.Context)
    ctx.author = MagicMock(spec=discord.Member)
    ctx.channel = MagicMock()
    ctx.command = MagicMock()
    ctx.command.name = "test_command"
    return ctx

@pytest.fixture
def mock_interaction():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.channel = MagicMock(spec=discord.TextChannel)
    interaction.guild = MagicMock(spec=discord.Guild)
    return interaction

class TestCog(BaseCommand):
    """Test cog description"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command()
    async def test_command(self, ctx):
        """Test command description"""
        pass

@pytest.mark.asyncio
async def test_base_command_help():
    """Test la génération de l'aide pour les commandes"""
    bot = MagicMock()
    cog = TestCog(bot)
    
    assert "Test cog description" in cog.__doc__
    assert "test_command" in cog.__doc__
    assert "Test command description" in cog.__doc__

@pytest.mark.asyncio
async def test_command_check_permission(mock_ctx):
    """Test la vérification des permissions"""
    # Simuler un manque de permission
    perms = MagicMock()
    perms.manage_messages = False
    mock_ctx.channel.permissions_for.return_value = perms
    mock_ctx.author.id = 123456789
    mock_ctx.channel.id = 987654321
    
    check = CommandCheck.has_permission("manage_messages")
    with pytest.raises(PermissionError) as exc_info:
        await check.predicate(mock_ctx)
    error = exc_info.value
    assert error.permission == "manage_messages"
    assert error.user_id == 123456789
    assert error.channel_id == 987654321
    
    # Simuler une permission valide
    perms.manage_messages = True
    assert await check.predicate(mock_ctx)

@pytest.mark.asyncio
async def test_command_error_handler(mock_bot, mock_ctx):
    """Test le gestionnaire d'erreurs de commande"""
    
    @command_error_handler
    async def test_command(self, ctx):
        raise ValueError("Test error")
    
    # Simuler une commande avec erreur
    cog = MagicMock()
    cog.bot = mock_bot
    await test_command(cog, mock_ctx)
    
    # Vérifier que l'erreur a été gérée
    mock_bot.error_handler.handle_error.assert_called_once()
    error = mock_bot.error_handler.handle_error.call_args[0][0]
    assert isinstance(error, CommandError)
    assert "Test error" in str(error)

@pytest.mark.asyncio
async def test_slash_command_group_creation(mock_bot):
    """Test la création d'un groupe de commandes slash"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="hello", description="Test command")
            async def hello_command(self, interaction: discord.Interaction):
                await interaction.response.send_message("Hello!")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Vérifier que le groupe est créé correctement
    assert isinstance(cog.group, app_commands.Group)
    assert cog.group.name == "test"
    assert len(cog.group.commands) == 1
    assert cog.group.commands[0].name == "hello"

@pytest.mark.asyncio
async def test_slash_command_execution(mock_bot, mock_interaction):
    """Test l'exécution d'une commande slash"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="hello", description="Test command")
            async def hello_command(self, interaction: discord.Interaction):
                await interaction.response.send_message("Hello!")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Exécuter la commande
    command = cog.group.commands[0]
    await command.callback(cog, mock_interaction)
    
    # Vérifier que la réponse a été envoyée
    mock_interaction.response.send_message.assert_called_once_with("Hello!")

@pytest.mark.asyncio
async def test_slash_command_error_handling(mock_bot, mock_interaction):
    """Test la gestion des erreurs pour une commande slash"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="error", description="Command with error")
            async def error_command(self, interaction: discord.Interaction):
                raise ValueError("Test error")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Exécuter la commande qui lève une erreur
    command = cog.group.commands[0]
    await command.callback(cog, mock_interaction)
    
    # Vérifier que l'erreur est gérée
    mock_bot.error_handler.handle_error.assert_called_once()
    args = mock_bot.error_handler.handle_error.call_args[0]
    assert isinstance(args[0], ValueError)
    assert str(args[0]) == "Test error"

@pytest.mark.asyncio
async def test_slash_command_help_setup(mock_bot):
    """Test la configuration de l'aide pour les commandes slash"""
    class TestCog(BaseCommand):
        """Test cog description"""
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="cmd1", description="First command")
            async def first_command(self, interaction: discord.Interaction):
                pass
            
            @self.group.command(name="cmd2", description="Second command")
            async def second_command(self, interaction: discord.Interaction):
                pass
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Vérifier que l'aide est configurée
    assert cog.__doc__ is not None
    assert "Test cog description" in cog.__doc__
    assert "cmd1" in str(cog.group.commands[0])
    assert "cmd2" in str(cog.group.commands[1])

@pytest.mark.asyncio
async def test_slash_command_group():
    """Test la création d'un groupe de commandes slash"""
    group = SlashCommandGroup(name="test", description="Test group")
    assert group.name == "test"
    assert group.description == "Test group"

@pytest.mark.asyncio
async def test_slash_command_group_with_validators(mock_bot, mock_interaction):
    """Test un groupe de commandes slash avec validation des paramètres"""
    
    group = SlashCommandGroup(name="test", description="Test group")
    
    # Ajouter des validateurs au groupe
    group.add_validator("test", "username", StringValidator("username", min_length=3))
    group.add_validator("test", "user_age", NumberValidator("user_age", min_value=0, max_value=150))
    
    # Test de validation des paramètres
    # Test avec des paramètres valides
    kwargs = {"username": "John", "user_age": 25}
    validated_kwargs = await group._validate_params("test", **kwargs)
    assert validated_kwargs["username"] == "John"
    assert validated_kwargs["user_age"] == 25
    
    # Test avec un nom trop court
    with pytest.raises(CommandError) as exc_info:
        await group._validate_params("test", username="Jo", user_age=25)
    assert "au moins 3 caractères" in str(exc_info.value)
    
    # Test avec un âge invalide
    with pytest.raises(CommandError) as exc_info:
        await group._validate_params("test", username="John", user_age=200)
    assert "inférieur ou égal à 150" in str(exc_info.value)

@pytest.mark.asyncio
async def test_slash_command_group_error_handling_with_validation(mock_bot, mock_interaction):
    """Test la gestion d'erreur avec validation des paramètres"""
    
    group = SlashCommandGroup(name="test")
    
    # Définir un gestionnaire d'erreur personnalisé
    async def custom_error_handler(interaction: discord.Interaction, error: Exception):
        if isinstance(error, CommandError):
            await interaction.response.send_message(f"Erreur : {error}")
        else:
            await interaction.response.send_message("Erreur inattendue")
    
    group.error_handler = custom_error_handler
    
    # Ajouter un validateur
    group.add_validator("test", "value", NumberValidator("value", min_value=0))
    
    # Simuler une erreur de validation
    kwargs = {"value": -1}
    with pytest.raises(CommandError) as exc_info:
        await group._validate_params("test", **kwargs)
    assert "supérieur ou égal à 0" in str(exc_info.value)
    
    # Simuler une erreur avec le gestionnaire
    error = ValueError("Test error")
    await group.on_error(mock_interaction, error)
    mock_interaction.response.send_message.assert_called_once_with("Erreur inattendue")

@pytest.mark.asyncio
async def test_create_slash_command(mock_bot, mock_interaction):
    """Test la création d'une commande slash"""
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
        
        @create_slash_command(name="test", description="Test command")
        async def test_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Test réussi")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Vérifier que la commande est créée correctement
    command = cog.test_command
    assert isinstance(command, app_commands.Command)
    assert command.name == "test"
    assert command.description == "Test command"
    
    # Simuler l'exécution de la commande
    result = await command.callback(cog, mock_interaction)
    assert result is True
    mock_interaction.response.send_message.assert_called_once_with("Test réussi")

@pytest.mark.asyncio
async def test_slash_command_check_permission(mock_interaction):
    """Test la vérification des permissions pour les commandes slash"""
    # Simuler un utilisateur membre
    mock_interaction.user = MagicMock(spec=discord.Member)
    mock_interaction.user.id = 123456789
    mock_interaction.channel = MagicMock()
    mock_interaction.channel_id = 987654321
    
    # Simuler un manque de permission
    perms = MagicMock()
    perms.manage_messages = False
    mock_interaction.channel.permissions_for.return_value = perms
    
    check = SlashCommandCheck.has_permission("manage_messages")
    with pytest.raises(PermissionError) as exc_info:
        await check(mock_interaction)
    error = exc_info.value
    assert error.permission == "manage_messages"
    assert error.user_id == 123456789
    assert error.channel_id == 987654321
    
    # Simuler une permission valide
    perms.manage_messages = True
    assert await check(mock_interaction)

@pytest.mark.asyncio
async def test_slash_command_check_role(mock_interaction):
    """Test la vérification des rôles pour les commandes slash"""
    # Simuler un utilisateur membre
    mock_interaction.user = MagicMock(spec=discord.Member)
    mock_interaction.user.id = 123456789
    mock_interaction.channel_id = 987654321
    mock_interaction.guild = MagicMock()
    
    # Créer un rôle de test
    role = MagicMock(spec=discord.Role)
    role.id = 123456789
    mock_interaction.guild.roles = [role]
    
    # Simuler un manque de rôle
    mock_interaction.user.roles = []
    check = SlashCommandCheck.has_role(role.id)
    with pytest.raises(PermissionError) as exc_info:
        await check(mock_interaction)
    error = exc_info.value
    assert error.permission == "role_123456789"
    assert error.user_id == 123456789
    assert error.channel_id == 987654321
    assert "Vous n'avez pas le rôle requis pour utiliser cette commande" == str(error)
    
    # Simuler un rôle valide
    mock_interaction.user.roles = [role]
    assert await check(mock_interaction)

@pytest.mark.asyncio
async def test_slash_command_check_owner(mock_interaction):
    """Test la vérification du propriétaire pour les commandes slash"""
    # Simuler l'application du bot
    mock_interaction.client = MagicMock()
    mock_interaction.client.application = MagicMock()
    mock_interaction.client.application.owner = MagicMock()
    mock_interaction.client.application.owner.id = 123456789
    mock_interaction.channel_id = 987654321
    
    # Simuler un utilisateur non propriétaire
    mock_interaction.user = MagicMock()
    mock_interaction.user.id = 111111111
    
    check = SlashCommandCheck.is_owner()
    with pytest.raises(PermissionError) as exc_info:
        await check(mock_interaction)
    error = exc_info.value
    assert error.permission == "owner"
    assert error.user_id == 111111111
    assert error.channel_id == 987654321
    assert "Seul le propriétaire du bot" in str(error)
    
    # Simuler le propriétaire
    mock_interaction.user.id = 123456789
    assert await check(mock_interaction)

@pytest.mark.asyncio
async def test_slash_command_with_checks(mock_bot, mock_interaction):
    """Test une commande slash avec des vérifications"""
    
    # Simuler un utilisateur membre avec permission
    mock_interaction.user = MagicMock(spec=discord.Member)
    mock_interaction.user.id = 123456789
    mock_interaction.channel = MagicMock()
    mock_interaction.channel_id = 987654321
    perms = MagicMock()
    perms.manage_messages = True
    mock_interaction.channel.permissions_for.return_value = perms
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
        
        @create_slash_command(
            name="test",
            description="Test command",
            checks=[SlashCommandCheck.has_permission("manage_messages")]
        )
        async def test_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Test réussi")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Vérifier que la commande est créée correctement
    command = cog.test_command
    assert isinstance(command, app_commands.Command)
    
    # Simuler l'exécution de la commande avec permission
    result = await command.callback(cog, mock_interaction)
    assert result is True
    mock_interaction.response.send_message.assert_called_once_with("Test réussi")
    
    # Réinitialiser le mock
    mock_interaction.response.send_message.reset_mock()
    
    # Simuler l'exécution de la commande sans permission
    perms.manage_messages = False
    with pytest.raises(PermissionError) as exc_info:
        await command.callback(cog, mock_interaction)
    error = exc_info.value
    assert error.permission == "manage_messages"
    assert error.user_id == 123456789
    assert error.channel_id == 987654321
    assert "n'a pas la permission" in str(error)

@pytest.mark.asyncio
async def test_slash_command_cooldown(mock_bot, mock_interaction):
    """Test le cooldown des commandes slash"""
    
    # Simuler une date de création pour l'interaction
    mock_interaction.created_at = MagicMock()
    mock_interaction.created_at.timestamp.return_value = 1000.0
    
    # Simuler un utilisateur
    mock_interaction.user = MagicMock()
    mock_interaction.user.id = 123456789
    
    # Simuler le client
    mock_interaction.client = MagicMock()
    mock_interaction.client._command_cooldowns = {}
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
        
        @create_slash_command(
            name="test",
            description="Test command"
        )
        @SlashCommandCheck.cooldown(rate=2, per=60.0)
        async def test_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Test réussi")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    command = cog.test_command
    
    # Première utilisation - devrait réussir
    result = await command.callback(cog, mock_interaction)
    assert result is True
    
    # Deuxième utilisation - devrait réussir
    result = await command.callback(cog, mock_interaction)
    assert result is True
    
    # Troisième utilisation - devrait échouer avec cooldown
    mock_interaction.created_at.timestamp.return_value = 1001.0
    with pytest.raises(CommandError) as exc_info:
        await command.callback(cog, mock_interaction)
    assert "cooldown" in str(exc_info.value)
    assert "59 secondes" in str(exc_info.value)
    
    # Après le cooldown - devrait réussir
    mock_interaction.created_at.timestamp.return_value = 1061.0
    result = await command.callback(cog, mock_interaction)
    assert result is True

@pytest.mark.asyncio
async def test_slash_command_cooldown_guild(mock_bot, mock_interaction):
    """Test le cooldown des commandes slash au niveau du serveur"""
    
    # Simuler une date de création pour l'interaction
    mock_interaction.created_at = MagicMock()
    mock_interaction.created_at.timestamp.return_value = 1000.0
    
    # Simuler un serveur
    mock_interaction.guild_id = 987654321
    
    # Simuler le client
    mock_interaction.client = MagicMock()
    mock_interaction.client._command_cooldowns = {}
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
        
        @create_slash_command(
            name="test",
            description="Test command"
        )
        @SlashCommandCheck.cooldown(rate=1, per=30.0, bucket_type=BucketType.guild)
        async def test_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Test réussi")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    command = cog.test_command
    
    # Première utilisation - devrait réussir
    result = await command.callback(cog, mock_interaction)
    assert result is True
    
    # Deuxième utilisation - devrait échouer avec cooldown
    mock_interaction.created_at.timestamp.return_value = 1001.0
    with pytest.raises(CommandError) as exc_info:
        await command.callback(cog, mock_interaction)
    assert "cooldown" in str(exc_info.value)
    assert "29 secondes" in str(exc_info.value)
    
    # Après le cooldown - devrait réussir
    mock_interaction.created_at.timestamp.return_value = 1031.0
    result = await command.callback(cog, mock_interaction)
    assert result is True

@pytest.mark.asyncio
async def test_slash_command_with_aliases(mock_bot, mock_interaction):
    """Test une commande slash avec des alias"""
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup(name="test", description="Test group")
        
        @create_slash_command(
            name="hello",
            description="Test command",
            aliases=["hi", "hey"]
        )
        async def hello_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Hello!")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    command = cog.hello_command
    
    # Vérifier que la commande est créée correctement
    assert isinstance(command, app_commands.Command)
    assert command.name == "hello"
    
    # Simuler l'exécution de la commande
    result = await command.callback(cog, mock_interaction)
    assert result is True
    mock_interaction.response.send_message.assert_called_once_with("Hello!")
    
    # Vérifier que les alias sont enregistrés
    if isinstance(cog.group, SlashCommandGroup):
        assert cog.group.get_command_name("hi") == "hello"
        assert cog.group.get_command_name("hey") == "hello"
        assert cog.group.get_command_usage("hello") == 1
        
        # Vérifier les alias
        aliases = cog.group.get_command_aliases("hello")
        assert len(aliases) == 2
        assert "hi" in aliases
        assert "hey" in aliases 