import discord
from discord.ext import commands
from discord import app_commands
from src.infrastructure.repositories.task_repository import TaskRepository
import logging

# Ce fichier est déprécié. Les commandes sont maintenant gérées dans tasks.py
# Gardé temporairement pour référence

class TaskCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.task_repository = TaskRepository()
        self.logger = logging.getLogger(__name__)

async def setup(bot: commands.Bot):
    # Les commandes sont désactivées car elles sont maintenant dans tasks.py
    pass 