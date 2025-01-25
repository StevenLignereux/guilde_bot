"""
Tests pour les alias des commandes slash
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from discord import app_commands
from src.infrastructure.commands.base import (
    BaseCommand, SlashCommandGroup, create_slash_command
)

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.error_handler = MagicMock()
    bot.error_handler.handle_error = AsyncMock()
    return bot

@pytest.fixture
def mock_interaction():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction

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

@pytest.mark.asyncio
async def test_slash_command_alias_usage_tracking(mock_bot, mock_interaction):
    """Test le suivi d'utilisation des commandes avec alias"""
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup(name="test", description="Test group")
        
        @create_slash_command(
            name="greet",
            description="Test command",
            aliases=["hello", "hi"]
        )
        async def greet_command(self, interaction: discord.Interaction):
            await interaction.response.send_message("Greetings!")
            return True
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    command = cog.greet_command
    
    # Simuler plusieurs utilisations de la commande
    await command.callback(cog, mock_interaction)  # Via nom principal
    await command.callback(cog, mock_interaction)  # Via nom principal
    
    # Vérifier le suivi d'utilisation
    if isinstance(cog.group, SlashCommandGroup):
        assert cog.group.get_command_usage("greet") == 2
        assert cog.group.get_command_usage("hello") == 2  # Même compteur que le nom principal
        assert cog.group.get_command_usage("hi") == 2     # Même compteur que le nom principal

@pytest.mark.asyncio
async def test_slash_command_duplicate_alias(mock_bot):
    """Test la gestion des alias en double"""
    
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup(name="test", description="Test group")
        
        @create_slash_command(
            name="cmd1",
            description="First command",
            aliases=["alias1"]
        )
        async def first_command(self, interaction: discord.Interaction):
            pass
        
        @create_slash_command(
            name="cmd2",
            description="Second command",
            aliases=["alias1"]  # Même alias que cmd1
        )
        async def second_command(self, interaction: discord.Interaction):
            pass
    
    # Vérifier que la création du cog lève une exception
    with pytest.raises(ValueError) as exc_info:
        TestCog(mock_bot)
    assert "déjà utilisé" in str(exc_info.value) 