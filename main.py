import discord
from discord.ext import commands
import asyncio
import logging
from src.config.config import Config, load_config
from src.infrastructure.config.database import init_db
from src.infrastructure.logging.logger import setup_logging
import os
from dotenv import load_dotenv
from src.infrastructure.commands.task_commands import TaskCommands
from src.application.services.task_service import TaskService

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class GuildeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self) -> None:
        """Configure le bot avant son démarrage"""
        try:
            # Configurer les commandes
            await TaskCommands(self).setup()
            logger.info("Commandes configurées avec succès")
            
            # Synchroniser les commandes avec Discord
            await self.tree.sync()
            logger.info("Commandes synchronisées avec Discord")
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du bot: {e}")
            raise

    async def on_ready(self):
        """Appelé quand le bot est prêt"""
        if self.user:
            logger.info(f"Bot connecté en tant que {self.user.name}")
        else:
            logger.error("Bot connecté mais self.user est None")

async def main():
    """Point d'entrée principal du bot"""
    try:
        # Configurer le logging
        setup_logging()
        logger.info("Logging configuré avec succès")
        
        # Charger la configuration
        config = load_config()
        logger.info("Configuration chargée avec succès")
        
        # Initialiser la base de données
        await init_db(config.database)
        logger.info("Base de données initialisée avec succès")
        
        # Créer et démarrer le bot
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN n'est pas défini dans les variables d'environnement")
            
        async with GuildeBot() as bot:
            await bot.start(token)
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
