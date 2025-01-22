import discord
from discord.ext import commands
from discord.ui import Button, View, Select, TextInput, Modal
import asyncio

# Dictionnaire pour stocker les listes de tâches
user_tasks = {}
task_id_counter = 1  # Compteur pour générer des IDs uniques

# Dictionnaire temporaire pour stocker la liste sélectionnée
selected_lists = {}

# Dictionnaire temporaire pour stocker la tâche sélectionnée
selected_tasks = {}


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commande pour afficher le menu principal
    @commands.command(name="tasks")
    async def tasks_menu(self, ctx):
        view = View()
        view.add_item(Button(label="Créer une liste",
                      style=discord.ButtonStyle.primary, custom_id="create_list"))
        view.add_item(Button(label="Afficher mes listes",
                      style=discord.ButtonStyle.secondary, custom_id="view_lists"))
        view.add_item(Button(label="Ajouter une tâche",
                      style=discord.ButtonStyle.success, custom_id="add_task"))
        view.add_item(Button(label="Modifier une tâche",
                      style=discord.ButtonStyle.danger, custom_id="edit_task"))
        await ctx.send("Que souhaitez-vous faire ?", view=view)

    # Gestion des interactions
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # Vérifier si l'interaction est de type composant (bouton, menu déroulant)
        if "component_type" in interaction.data:
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
        # Vérifier si l'interaction est de type modal
        elif interaction.type == discord.InteractionType.modal_submit:
            custom_id = interaction.data.get("custom_id")
            if custom_id == "create_list_modal":
                await self.handle_create_list_modal(interaction)
            elif custom_id == "add_task_modal":
                await self.handle_add_task_modal(interaction)
            elif custom_id == "edit_task_modal":
                await self.handle_edit_task_modal(interaction)

    # Créer une liste
    async def handle_create_list(self, interaction):
        # Créer un modal pour le nom de la liste
        modal = Modal(title="Créer une liste")
        modal.add_item(TextInput(label="Nom de la liste",
                       placeholder="Ex: Travail", custom_id="list_name"))
        modal.custom_id = "create_list_modal"

        # Envoyer le modal
        await interaction.response.send_modal(modal)

    # Gérer la soumission du modal de création de liste
    async def handle_create_list_modal(self, interaction):
        # Récupérer le nom de la liste depuis le modal
        list_name = interaction.data["components"][0]["components"][0]["value"]
        user_id = str(interaction.user.id)

        # Vérifier si la liste existe déjà
        if user_id not in user_tasks:
            user_tasks[user_id] = {}
        if list_name in user_tasks[user_id]:
            await interaction.response.send_message(f"La liste `{list_name}` existe déjà.", ephemeral=True)
            return

        # Créer la liste
        user_tasks[user_id][list_name] = []
        await interaction.response.send_message(f"Liste `{list_name}` créée avec succès !", ephemeral=True)

    # Afficher les listes
    async def handle_view_lists(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        # Répondre à l'interaction une seule fois
        await interaction.response.send_message("Chargement de vos listes...", ephemeral=True)

        # Envoyer chaque liste en utilisant followup.send
        for list_name, tasks in user_tasks[user_id].items():
            task_list = []
            view = View()  # Créer une View pour les boutons de cette liste

            # Calculer le nombre de tâches terminées
            completed_tasks = sum(1 for task in tasks if task["completed"])
            total_tasks = len(tasks)

            # Définir la couleur de l'embed en fonction de l'état des tâches
            if completed_tasks == total_tasks and total_tasks > 0:
                embed_color = discord.Color.green()  # Toutes les tâches sont terminées
            elif completed_tasks == 0 and total_tasks > 0:
                embed_color = discord.Color.red()  # Aucune tâche n'est terminée
            else:
                embed_color = discord.Color.orange()  # Certaines tâches sont terminées

            embed = discord.Embed(title=f"📋 - {list_name}", color=embed_color)

            for task in tasks:
                # Vérifier si la tâche a un ID
                if "id" not in task:
                    task["id"] = task_id_counter
                    task_id_counter += 1

                # Texte rayé si la tâche est terminée
                task_text = f"~~{task['task']}~~" if task["completed"] else task["task"]
                status = "✅" if task["completed"] else "❌"
                
                # Créer un bouton interactif
                button = Button(
                    style=discord.ButtonStyle.secondary,
                    emoji=status,
                    custom_id=f"task_toggle_{task['id']}"
                )
                button.callback = lambda i, t=task: self.toggle_task(i, t, list_name)
                view.add_item(button)
                
                task_list.append(f"{status} {task_text}")

            embed.add_field(name="Tâches", value="\n".join(task_list) or "Aucune tâche", inline=False)
            
            # Ajouter un champ pour le statut global de la liste
            embed.add_field(name="Statut", value=f"{completed_tasks}/{total_tasks} tâches terminées", inline=False)
        
            # Envoyer la liste avec followup.send
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def toggle_task(self, interaction, task, list_name):
        user_id = str(interaction.user.id)
        # Inverser le statut de la tâche
        task["completed"] = not task["completed"]

        # Mettre à jour l'emoji du bouton
        new_status = "✅" if task["completed"] else "❌"

        # Mettre à jour le message
        await self.update_task_message(interaction, list_name)

    async def update_task_message(self, interaction, list_name):
        user_id = str(interaction.user.id)
        embed = discord.Embed(title="📋 Vos listes de tâches",
                              color=discord.Color.blue())

        for list_name, tasks in user_tasks[user_id].items():
            task_list = []
            view = View()

            for task in tasks:
                task_text = f"~~{
                    task['task']}~~" if task["completed"] else task["task"]
                status = "✅" if task["completed"] else "❌"

                button = Button(
                    style=discord.ButtonStyle.secondary,
                    emoji=status,
                    custom_id=f"task_toggle_{task['id']}"
                )
                button.callback = lambda i, t=task: self.toggle_task(
                    i, t, list_name)
                view.add_item(button)

                task_list.append(f"{status} {task_text}")

            embed.add_field(name=list_name, value="\n".join(
                task_list) or "Aucune tâche", inline=False)

        await interaction.response.edit_message(embed=embed, view=view)

    # Ajouter une tâche
    async def handle_add_task(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        # Créer un menu déroulant pour choisir une liste
        select = Select(placeholder="Choisissez une liste", options=[
            discord.SelectOption(label=list_name) for list_name in user_tasks[user_id].keys()
        ])
        view = View()
        view.add_item(select)
        await interaction.response.send_message("À quelle liste voulez-vous ajouter une tâche ?", view=view, ephemeral=True)

        # Stocker la liste sélectionnée dans le dictionnaire temporaire
        selected_lists[user_id] = None

        # Attendre que l'utilisateur sélectionne une liste
        def check(interaction):
            return interaction.data["custom_id"] == select.custom_id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Temps écoulé. Veuillez réessayer.", ephemeral=True)
            return

        # Stocker la liste sélectionnée
        list_name = interaction.data["values"][0]
        selected_lists[user_id] = list_name

        # Créer un modal pour ajouter une tâche
        modal = Modal(title="Ajouter une tâche")
        modal.add_item(TextInput(label="Description de la tâche",
                       placeholder="Ex: Finir le rapport", custom_id="task_description"))
        modal.custom_id = "add_task_modal"
        await interaction.response.send_modal(modal)

    # Gérer la soumission du modal d'ajout de tâche
    async def handle_add_task_modal(self, interaction):
        user_id = str(interaction.user.id)

        # Récupérer la liste sélectionnée depuis le dictionnaire temporaire
        if user_id not in selected_lists or not selected_lists[user_id]:
            await interaction.response.send_message("Aucune liste sélectionnée. Veuillez réessayer.", ephemeral=True)
            return

        list_name = selected_lists[user_id]

        # Récupérer la description de la tâche depuis le modal
        task_description = interaction.data["components"][0]["components"][0]["value"]

        # Vérifier si la liste existe toujours
        if user_id not in user_tasks or list_name not in user_tasks[user_id]:
            await interaction.response.send_message("La liste sélectionnée n'existe plus.", ephemeral=True)
            return

        # Ajouter un ID unique à la tâche
        global task_id_counter
        task_id = task_id_counter
        task_id_counter += 1

        # Ajouter la tâche à la liste
        user_tasks[user_id][list_name].append(
            {"id": task_id, "task": task_description, "completed": False})
        await interaction.response.send_message(f"Tâche ajoutée à la liste `{list_name}` : {task_description}", ephemeral=True)

        # Nettoyer le dictionnaire temporaire
        del selected_lists[user_id]

    # Modifier une tâche
    async def handle_edit_task(self, interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_tasks or not user_tasks[user_id]:
            await interaction.response.send_message("Vous n'avez aucune liste de tâches.", ephemeral=True)
            return

        # Créer un menu déroulant pour choisir une liste
        select = Select(placeholder="Choisissez une liste", options=[
            discord.SelectOption(label=list_name) for list_name in user_tasks[user_id].keys()
        ])
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Dans quelle liste se trouve la tâche à modifier ?", view=view, ephemeral=True)

        # Attendre que l'utilisateur sélectionne une liste
        def check(interaction):
            return interaction.data["custom_id"] == select.custom_id

        try:
            interaction = await self.bot.wait_for("interaction", check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Temps écoulé. Veuillez réessayer.", ephemeral=True)
            return

        # Récupérer la liste sélectionnée
        list_name = interaction.data["values"][0]
        tasks = user_tasks[user_id][list_name]
        if not tasks:
            await interaction.response.send_message("Cette liste ne contient aucune tâche.", ephemeral=True)
            return

        # Créer un menu déroulant pour choisir une tâche
        select = Select(placeholder="Choisissez une tâche", options=[
            discord.SelectOption(label=f"{i + 1}. {task['task']}", value=str(i)) for i, task in enumerate(tasks)
        ])
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Quelle tâche voulez-vous modifier ?", view=view, ephemeral=True)

        # Attendre que l'utilisateur sélectionne une tâche
        interaction = await self.bot.wait_for("interaction", check=check)
        task_index = int(interaction.data["values"][0])

        # Stocker la liste et la tâche sélectionnées dans le dictionnaire temporaire
        selected_tasks[user_id] = {
            "list_name": list_name, "task_index": task_index}

        # Créer un modal pour modifier la tâche
        modal = Modal(title="Modifier la tâche")
        modal.add_item(TextInput(label="Nouvelle description",
                                 placeholder=tasks[task_index]["task"], custom_id="new_task_description"))
        modal.custom_id = "edit_task_modal"
        await interaction.response.send_modal(modal)

    # Gérer la soumission du modal de modification de tâche
    async def handle_edit_task_modal(self, interaction):
        user_id = str(interaction.user.id)

        # Récupérer la liste et la tâche sélectionnées depuis le dictionnaire temporaire
        if user_id not in selected_tasks:
            await interaction.response.send_message("Aucune tâche sélectionnée. Veuillez réessayer.", ephemeral=True)
            return

        list_name = selected_tasks[user_id]["list_name"]
        task_index = selected_tasks[user_id]["task_index"]

        # Récupérer la nouvelle description de la tâche depuis le modal
        new_task_description = interaction.data["components"][0]["components"][0]["value"]

        # Vérifier si la liste existe toujours
        if user_id not in user_tasks or list_name not in user_tasks[user_id]:
            await interaction.response.send_message("La liste sélectionnée n'existe plus.", ephemeral=True)
            return

        # Modifier la tâche
        user_tasks[user_id][list_name][task_index]["task"] = new_task_description
        await interaction.response.send_message(f"Tâche modifiée : {new_task_description}", ephemeral=True)

        # Nettoyer le dictionnaire temporaire
        del selected_tasks[user_id]

# Fonction pour ajouter le cog au bot


async def setup(bot):
    await bot.add_cog(Tasks(bot))
