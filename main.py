import discord
from dotenv import load_dotenv
import os
import logging
from discord.ext import commands

# Configurer le logging
LOG_LEVEL = logging.INFO
logging.basicConfig(level=LOG_LEVEL)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Fonction pour récupérer les variables d'environnement


def get_env_variable(name, default=None, required=True):
    value = os.getenv(name, default)
    if required and value is None:
        logging.error(f"La variable d'environnement {name} est manquante.")
        raise EnvironmentError(f"La variable d'environnement {
                               name} est manquante.")
    return value


TOKEN = get_env_variable('TOKEN')
CHANNEL_ID = int(get_env_variable('CHANNEL_ID'))
SOCIAL_ID = int(get_env_variable('SOCIAL_ID'))
OTHER_BOT_COMMAND = get_env_variable('OTHER_BOT_COMMAND', required=False)
TWITCH_CLIENT_ID = get_env_variable('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = get_env_variable('TWITCH_CLIENT_SECRET')
TWITCH_USERNAME = get_env_variable('TWITCH_USERNAME')
WELCOME_CHANNEL_ID = int(get_env_variable('WELCOME_CHANNEL_ID'))
WELCOME_IMAGE_PATH = get_env_variable('WELCOME_IMAGE_PATH')
FONT_PATH = get_env_variable('FONT_PATH')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Activer l'intention de contenu des messages
bot = commands.Bot(command_prefix='!', intents=intents)


async def main():
    # Charger les cogs
    await bot.load_extension('cogs.events')
    await bot.load_extension('cogs.commands')
    await bot.load_extension('cogs.news')
    await bot.load_extension('cogs.streams')

    # Démarrer le bot
    await bot.start(TOKEN)

# Exécuter la fonction principale
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
