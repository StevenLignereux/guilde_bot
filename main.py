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
import sys
from aiohttp import web

# Configuration du logger
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Charger les variables d'environnement
load_dotenv()

class GuildeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self) -> None:
        """Configure le bot avant son démarrage"""
        try:
            # Ajouter le cog TaskCommands
            task_commands = TaskCommands(self)
            await self.add_cog(task_commands)
            await task_commands.setup()
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
            print("=== BOT DÉMARRÉ ===")
            print(f"Nom du bot : {self.user.name}")
            print(f"ID du bot : {self.user.id}")
            print(f"Version Discord.py : {discord.__version__}")
            print("\n=== INTENTS ACTIVÉS ===")
            print(f"Members Intent: {self.intents.members}")
            print(f"Message Content Intent: {self.intents.message_content}")
            print(f"Guilds Intent: {self.intents.guilds}")
            
            print("\n=== COGS CHARGÉS ===")
            for cog in self.cogs:
                print(f"✅ {cog}")
            
            print("\n=== SERVEURS CONNECTÉS ===")
            for guild in self.guilds:
                print(f"- {guild.name} (ID: {guild.id})")
            
            print("\n=== CONFIGURATION ===")
            print(f"WELCOME_CHANNEL_ID: {os.getenv('WELCOME_CHANNEL_ID')}")
            channel = self.get_channel(int(os.getenv('WELCOME_CHANNEL_ID', '0')))
            if channel:
                print(f"✅ Canal de bienvenue trouvé : {getattr(channel, 'name', str(channel))}")
            else:
                print("❌ Canal de bienvenue non trouvé")
        else:
            logger.error("Bot connecté mais self.user est None")

async def load_extensions(bot):
    print("\n=== CHARGEMENT DES EXTENSIONS ===")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Extension chargée : {filename}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {filename}: {str(e)}")

async def start_server():
    """Démarre le serveur web"""
    app = web.Application()
    
    async def health_check(_):
        return web.Response(text="Bot is running")
    
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Démarrage du serveur sur le port {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"Serveur web démarré sur le port {port}")
    return runner

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
        
        # Démarrer le serveur web
        runner = await start_server()
        logger.info("Serveur web démarré")
        
        # Créer et démarrer le bot
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN n'est pas défini dans les variables d'environnement")
            
        async with GuildeBot() as bot:
            await load_extensions(bot)
            print("\n=== CONNEXION AU SERVEUR DISCORD ===")
            try:
                await bot.start(token)
            finally:
                await runner.cleanup()
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n=== ARRÊT DU BOT ===")
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {str(e)}")
        logger.error("Erreur critique", exc_info=True)
