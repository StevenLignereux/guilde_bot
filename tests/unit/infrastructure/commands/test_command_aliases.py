"""
Tests pour les alias des commandes slash
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from discord import app_commands
from src.infrastructure.commands.base import BaseCommand, SlashCommandGroup

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
    interaction.user = MagicMock(spec=discord.Member)
    interaction.channel = MagicMock(spec=discord.TextChannel)
    interaction.guild = MagicMock(spec=discord.Guild)
    return interaction

@pytest.mark.asyncio
async def test_slash_command_with_aliases(mock_bot, mock_interaction):
    """Test l'utilisation des alias pour une commande slash"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="hello", description="Test command")
            async def hello_command(self, interaction: discord.Interaction):
                await interaction.response.send_message("Hello!")
            
            # Ajouter des alias
            self.group.add_alias("hello", "hi")
            self.group.add_alias("hello", "hey")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Vérifier les alias
    assert set(cog.group.get_command_aliases("hello")) == {"hi", "hey"}
    
    # Tester l'exécution via un alias
    mock_interaction.command = MagicMock()
    mock_interaction.command.name = "hi"
    
    # Exécuter la commande via l'alias
    await cog.hello_command(mock_interaction)
    
    # Vérifier que la réponse a été envoyée
    mock_interaction.response.send_message.assert_called_once_with("Hello!")

@pytest.mark.asyncio
async def test_slash_command_alias_usage_tracking(mock_bot, mock_interaction):
    """Test le suivi d'utilisation des alias de commandes"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="hello", description="Test command")
            async def hello_command(self, interaction: discord.Interaction):
                self.group.track_command_usage(interaction.command.name)
                await interaction.response.send_message("Hello!")
            
            # Ajouter un alias
            self.group.add_alias("hello", "hi")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Exécuter la commande avec différents noms
    mock_interaction.command = MagicMock()
    
    # Via le nom principal
    mock_interaction.command.name = "hello"
    await cog.hello_command(mock_interaction)
    
    # Via l'alias
    mock_interaction.command.name = "hi"
    await cog.hello_command(mock_interaction)
    
    # Vérifier le suivi d'utilisation
    assert cog.group.get_command_usage("hello") == 1
    assert cog.group.get_command_usage("hi") == 1
    assert mock_interaction.response.send_message.call_count == 2

@pytest.mark.asyncio
async def test_slash_command_duplicate_alias(mock_bot):
    """Test la gestion des alias en double"""
    class TestCog(BaseCommand):
        def __init__(self, bot):
            super().__init__(bot)
            self.group = SlashCommandGroup("test", "Test group")
            
            @self.group.command(name="hello", description="Test command")
            async def hello_command(self, interaction: discord.Interaction):
                await interaction.response.send_message("Hello!")
            
            @self.group.command(name="greet", description="Another command")
            async def greet_command(self, interaction: discord.Interaction):
                await interaction.response.send_message("Greetings!")
    
    # Créer une instance du cog
    cog = TestCog(mock_bot)
    
    # Ajouter un alias
    cog.group.add_alias("hello", "hi")
    
    # Tenter d'ajouter le même alias à une autre commande
    with pytest.raises(ValueError) as exc_info:
        cog.group.add_alias("greet", "hi")
    
    assert "L'alias 'hi' est déjà utilisé" in str(exc_info.value) 