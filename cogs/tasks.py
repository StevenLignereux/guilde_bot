import discord
from discord.ext import commands
from discord.ui import Button, View, Select, TextInput, Modal
import asyncio

# Dictionnaire pour stocker les listes de tâches
user_tasks = {}

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commande pour afficher le menu principal
    @commands.command(name="tasks")
    async def tasks_menu(self, ctx):
        view = View()
        view.add_item(Button(label="Créer une liste", style=discord.ButtonStyle.primary, custom_id="create_list"))
        view.add_item(Button(label="Afficher mes listes", style=discord.ButtonStyle.secondary, custom_id="view_lists"))
        view.add_item(Button(label="Ajouter une tâche", style=discord.ButtonStyle.success, custom_id="add_task"))
        view.add_item(Button(label="Modifier une tâche", style=discord.ButtonStyle.danger, custom_id="edit_task"))
        await ctx.send("Que souhaitez-vous faire ?", view=view)

    # Gestion des interactions avec les boutons
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data["component_type"] == 2:  # Bouton cliqué
            custom_id = interaction.data["custom_id"]
            if custom_id == "create_list":
                await self.handle_create_list(interaction)
            elif custom_id == "view_lists":
                await self.handle_view_lists(interaction)
            elif custom_id == "add_task":
                await self.handle_add_task(interaction)
            elif custom_id == "edit_task":
                await self.handle_edit_task(interaction)

    # Créer une liste
    async def handle_create_list(self, interaction):
        # Envoyer une réponse initiale à l'interaction
        await interaction.response.send_message("Création de la liste en cours...", ephemeral=True)

        # Créer un modal pour le nom de la liste
        modal = Modal(title="Créer une liste")
        modal.add_item(TextInput(label="Nom de la liste", placeholder="Ex: Travail", custom_id="list_name"))
        modal.custom_id = "create_list_modal"
        await interaction.followup.send(modal=modal, ephemeral=True)

        # Attendre la soumission du modal
        try:
            modal_interaction = await self.bot.wait_for(
                "interaction",
                check=lambda i: i.data.get("custom_id") == "create_list_modal",
                timeout=60  # Timeout de 60 secondes
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("Temps écoulé. Veuillez réessayer.", ephemeral=True)
            return

        # Récupérer le nom de la liste depuis le modal
        list_name = modal_interaction.data["components"][0]["components"][0]["value"]
        user_id = str(interaction.user.id)

        # Vérifier si la liste existe déjà
        if user_id not in user_tasks:
            user_tasks[user_id] = {}
        if list_name in user_tasks[user_id]:
            await modal_interaction.response.send_message(f"La liste `{list_name}` existe déjà.", ephemeral=True)
            return

        # Créer la liste
        user_tasks[user_id][list_name] = []
        await modal_interaction.response.send_message(f"Liste `{list_name}` créée avec succès !", ephemeral=True)

    # Afficher les listes
    async def handle_view_lists(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        embed = discord.Embed(title="📋 Vos listes de tâches", color=discord.Color.blue())
        for list_name, tasks in user_tasks[user_id].items():
            task_list = "\n".join(
                [f"{'✅' if task['completed'] else '❌'} {task['task']}" for task in tasks]
            )
            embed.add_field(name=list_name, value=task_list or "Aucune tâche", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Ajouter une tâche
    async def handle_add_task(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        select = Select(placeholder="Choisissez une liste", options=[
            discord.SelectOption(label=list_name) for list_name in user_tasks[user_id].keys()
        ])
        view = View()
        view.add_item(select)
        await interaction.response.send_message("À quelle liste voulez-vous ajouter une tâche ?", view=view, ephemeral=True)

        def check(interaction):
            return interaction.data["custom_id"] == select.custom_id

        interaction = await self.bot.wait_for("interaction", check=check)
        list_name = interaction.data["values"][0]
        modal = Modal(title="Ajouter une tâche")
        modal.add_item(TextInput(label="Description de la tâche", placeholder="Ex: Finir le rapport"))
        await interaction.response.send_modal(modal)

        interaction = await self.bot.wait_for("interaction", check=check)
        task = interaction.data["components"][0]["components"][0]["value"]
        user_tasks[user_id][list_name].append({"task": task, "completed": False})
        await interaction.followup.send(f"Tâche ajoutée à la liste `{list_name}` : {task}", ephemeral=True)

    # Modifier une tâche
    async def handle_edit_task(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        select = Select(placeholder="Choisissez une liste", options=[
            discord.SelectOption(label=list_name) for list_name in user_tasks[user_id].keys()
        ])
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Dans quelle liste se trouve la tâche à modifier ?", view=view, ephemeral=True)

        def check(interaction):
            return interaction.data["custom_id"] == select.custom_id

        interaction = await self.bot.wait_for("interaction", check=check)
        list_name = interaction.data["values"][0]
        tasks = user_tasks[user_id][list_name]
        if not tasks:
            await interaction.followup.send("Cette liste ne contient aucune tâche.", ephemeral=True)
            return

        select = Select(placeholder="Choisissez une tâche", options=[
            discord.SelectOption(label=f"{i + 1}. {task['task']}", value=str(i)) for i, task in enumerate(tasks)
        ])
        view = View()
        view.add_item(select)
        await interaction.followup.send("Quelle tâche voulez-vous modifier ?", view=view, ephemeral=True)

        interaction = await self.bot.wait_for("interaction", check=check)
        task_index = int(interaction.data["values"][0])
        modal = Modal(title="Modifier la tâche")
        modal.add_item(TextInput(label="Nouvelle description", placeholder=tasks[task_index]["task"]))
        await interaction.response.send_modal(modal)

        interaction = await self.bot.wait_for("interaction", check=check)
        new_task = interaction.data["components"][0]["components"][0]["value"]
        tasks[task_index]["task"] = new_task
        await interaction.followup.send(f"Tâche modifiée : {new_task}", ephemeral=True)

# Fonction pour ajouter le cog au bot
async def setup(bot):
    await bot.add_cog(Tasks(bot))