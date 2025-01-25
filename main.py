import discord
import logging
from discord.ext import commands
from keep_alive import keep_alive
import asyncio
from src.config.environment import load_environment
from src.infrastructure.config.database import init_db

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger la configuration
try:
    config = load_environment()
    logger.info("Configuration chargée avec succès")
except Exception as e:
    logger.error(f"Erreur lors du chargement de la configuration : {str(e)}")
    raise

# Configuration du bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Commandes slash synchronisées : {len(synced)} commande(s)')
    except Exception as e:
        print(f'Erreur lors de la synchronisation des commandes : {e}')

async def setup():
    try:
        logger.info("Initialisation de la base de données...")
        init_db()  # Initialise la base de données en premier
        logger.info("Base de données initialisée avec succès")
        
        logger.info("Chargement des extensions...")
        await bot.load_extension('cogs.events')
        await bot.load_extension('cogs.commands')
        await bot.load_extension('cogs.tasks')
        await bot.load_extension('cogs.news')
        await bot.load_extension('cogs.stream')
        logger.info("Extensions chargées avec succès")
        
        keep_alive()
        token = config.get('DISCORD_TOKEN')
        if not token:
            raise ValueError("Token Discord manquant dans la configuration")
        await bot.start(token)
    except Exception as e:
        logger.error(f"Erreur lors du setup : {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(setup())
    except KeyboardInterrupt:
        logger.info("Arrêt du bot...")
    except Exception as e:
        logger.error(f"Erreur fatale : {str(e)}")
