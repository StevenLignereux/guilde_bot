import discord
from discord.ext import commands
from discord.ui import Button, View, Select, TextInput, Modal
import asyncio
import traceback
from src.application.services.task_service import TaskService

# Structures de données
user_tasks = {}
task_id_counter = 1
selected_lists = {}
selected_tasks = {}


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.task_service = TaskService()
        # Ajout des paramètres requis name et callback
        self.ctx_menu = discord.app_commands.ContextMenu(
            name="Toggle Task",  # Nom du menu contextuel
            callback=self.toggle_task_context  # Fonction de callback
        )
        self.bot.tree.add_command(self.ctx_menu)  # Ajout au command tree

    async def toggle_task_context(self, interaction: discord.Interaction, member: discord.Member):
        """Callback pour le menu contextuel"""
        # Implémentez votre logique ici
        await interaction.response.send_message(f"Menu contextuel déclenché pour {member.display_name}", ephemeral=True)

    # region Commandes Principales
    @commands.command(name="tasks")
    async def tasks_menu(self, ctx):
        """Affiche le menu principal des tâches"""
        view = View()
        buttons = [
            ("Créer une liste", "create_list", discord.ButtonStyle.primary),
            ("Afficher mes listes", "view_lists", discord.ButtonStyle.secondary),
            ("Ajouter une tâche", "add_task", discord.ButtonStyle.success),
            ("Modifier une tâche", "edit_task", discord.ButtonStyle.danger)
        ]

        for label, custom_id, style in buttons:
            view.add_item(
                Button(label=label, custom_id=custom_id, style=style))

        await ctx.send("Que souhaitez-vous faire ?", view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Gestionnaire central des interactions"""
        try:
            if interaction.type == discord.InteractionType.component:
                await self.handle_component_interaction(interaction)
            elif interaction.type == discord.InteractionType.modal_submit:
                await self.handle_modal_submission(interaction)
        except Exception as e:
            self.log_error(e, "on_interaction")
            await self.send_error(interaction)

    async def handle_component_interaction(self, interaction):
        """Gère les interactions des composants UI"""
        handlers = {
            "create_list": self.handle_create_list,
            "view_lists": self.handle_view_lists,
            "add_task": self.handle_add_task,
            "edit_task": self.handle_edit_task
        }
        custom_id = interaction.data.get("custom_id")
        if handler := handlers.get(custom_id):
            await handler(interaction)

    async def handle_modal_submission(self, interaction):
        """Gère la soumission des modals"""
        handlers = {
            "create_list_modal": self.handle_create_list_modal,
            "add_task_modal": self.handle_add_task_modal,
            "edit_task_modal": self.handle_edit_task_modal
        }
        custom_id = interaction.data.get("custom_id")
        if handler := handlers.get(custom_id):
            await handler(interaction)
    # endregion

    # region Gestion des Listes
    async def handle_create_list(self, interaction):
        """Lance la création d'une nouvelle liste"""
        modal = Modal(title="Créer une liste")
        modal.add_item(TextInput(
            label="Nom de la liste",
            placeholder="Ex: Travail",
            custom_id="list_name"
        ))
        modal.custom_id = "create_list_modal"
        await interaction.response.send_modal(modal)

    async def handle_create_list_modal(self, interaction):
        """Traite la création d'une liste"""
        try:
            # Différer la réponse immédiatement pour éviter l'expiration
            await interaction.response.defer(ephemeral=True)
            
            list_name = interaction.data["components"][0]["components"][0]["value"].strip()
            user_id = str(interaction.user.id)

            success, message, task_list = await self.task_service.create_list(list_name, user_id)
            
            # Utiliser followup.send puisque nous avons différé la réponse
            await interaction.followup.send(
                f"✅ Liste '{list_name}' créée !" if success else f"❌ {message}",
                ephemeral=True
            )

        except Exception as e:
            self.log_error(e, "create_list_modal")
            try:
                await interaction.followup.send("❌ Une erreur s'est produite", ephemeral=True)
            except Exception as e:
                print(f"Impossible d'envoyer le message d'erreur : {str(e)}")

    async def handle_view_lists(self, interaction):
        """Affiche toutes les listes de l'utilisateur"""
        try:
            user_id = str(interaction.user.id)
            lists = await self.task_service.get_user_lists(user_id)
            
            if not lists:
                return await interaction.response.send_message("ℹ️ Aucune liste disponible", ephemeral=True)

            await interaction.response.defer(ephemeral=True)

            for task_list in lists:
                embed, view = await self.build_list_interface(task_list)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            self.log_error(e, "view_lists")
            await self.send_error(interaction)

    async def build_list_interface(self, task_list):
        """Construit l'interface d'une liste"""
        embed = discord.Embed(
            title=f"📋 {task_list.name}",
            color=self.get_list_color(task_list.tasks)
        )
        view = View(timeout=None)

        completed = sum(1 for t in task_list.tasks if t.completed)
        total = len(task_list.tasks)

        tasks_display = []
        for task in task_list.tasks:
            task_str = f"~~{task.description}~~" if task.completed else task.description
            btn = self.create_task_button(task)
            view.add_item(btn)
            tasks_display.append(f"{btn.emoji} {task_str}")

        embed.add_field(name="Tâches", value="\n".join(tasks_display) or "Aucune tâche", inline=False)
        embed.add_field(name="Statut", value=f"{completed}/{total} terminées", inline=False)

        return embed, view

    def get_list_color(self, tasks):
        """Détermine la couleur selon l'avancement"""
        if not tasks:
            return discord.Color.light_grey()
            
        completed = sum(1 for t in tasks if t.completed)
        ratio = completed / len(tasks)
        
        return discord.Color.from_rgb(
            int(255 * (1 - ratio)),
            int(255 * ratio),
            0
        )

    def create_task_button(self, task):
        """Crée un bouton de tâche interactif"""
        button = Button(
            style=discord.ButtonStyle.secondary,
            emoji="✅" if task.completed else "❌",
            custom_id=f"task_toggle_{task.id}"
        )
        button.callback = lambda i, t=task: self.toggle_task_status(i, t.id)
        return button
    # endregion

    # region Gestion des Tâches
    async def toggle_task_status(self, interaction, task_id):
        """Bascule l'état d'une tâche"""
        try:
            task = await self.task_service.toggle_task(task_id)
            if task:
                task_list = task.task_list
                embed, view = await self.build_list_interface(task_list)
                await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            self.log_error(e, "toggle_task")
            await self.send_error(interaction)

    async def handle_add_task(self, interaction):
            """Lance l'ajout de tâches"""
            try:
                user_id = str(interaction.user.id)
                lists = user_tasks.get(user_id, {})

                if not lists:
                    return await interaction.response.send_message("ℹ️ Créez d'abord une liste", ephemeral=True)

                select = Select(placeholder="Choisissez une liste")
                select.options = [discord.SelectOption(label=name) for name in lists.keys()]

                async def select_callback(interaction):
                    try:
                        # Stockage de la liste sélectionnée
                        selected_lists[str(interaction.user.id)] = interaction.data["values"][0]
                        
                        # Création du modal avec custom_id
                        modal = Modal(title="Ajouter des tâches", custom_id="add_task_modal")
                        for i in range(1, 6):
                            modal.add_item(TextInput(
                                label=f"Tâche {i}",
                                placeholder="[Optionnel]",
                                required=False,
                                custom_id=f"task_{i}"  # Ajout d'un custom_id unique
                            ))
                        await interaction.response.send_modal(modal)
                    except Exception as e:
                        self.log_error(e, "add_task_select")
                        await self.send_error(interaction)

                select.callback = select_callback
                view = View()
                view.add_item(select)

                await interaction.response.send_message("Choisissez une liste :", view=view, ephemeral=True)

            except Exception as e:
                self.log_error(e, "add_task")
                await self.send_error(interaction)

    async def handle_add_task_modal(self, interaction):
        """Traite l'ajout de tâches (version corrigée)"""
        try:
            user_id = str(interaction.user.id)
            list_name = selected_lists.get(user_id)
            
            if not list_name or not user_tasks.get(user_id) or list_name not in user_tasks[user_id]:
                return await interaction.response.send_message("⚠️ Liste invalide", ephemeral=True)

            # Récupération des valeurs du modal
            tasks = []
            for component in interaction.data["components"]:
                task_input = component["components"][0]
                if task_input["value"].strip():
                    tasks.append(task_input["value"].strip())

            if not tasks:
                return await interaction.response.send_message("ℹ️ Aucune tâche valide", ephemeral=True)

            # Ajout des tâches
            global task_id_counter
            for task_desc in tasks:
                user_tasks[user_id][list_name].append({
                    "id": task_id_counter,
                    "task": task_desc,
                    "completed": False
                })
                task_id_counter += 1

            await interaction.response.send_message(f"✅ {len(tasks)} tâche(s) ajoutée(s) à '{list_name}'!", ephemeral=True)
            del selected_lists[user_id]  # Nettoyage

        except Exception as e:
            self.log_error(e, "add_task_modal")
            await self.send_error(interaction)


    async def handle_edit_task(self, interaction):
        """Gère la modification d'une tâche"""
        try:
            user_id = str(interaction.user.id)
            lists = user_tasks.get(user_id, {})

            if not lists:
                return await interaction.response.send_message("ℹ️ Créez d'abord une liste", ephemeral=True)

            # Créez un menu déroulant pour sélectionner la liste
            select = Select(placeholder="Choisissez une liste")
            select.options = [discord.SelectOption(label=name) for name in lists.keys()]

            async def select_callback(interaction):
                try:
                    selected_list = interaction.data["values"][0]
                    tasks = lists[selected_list]

                    if not tasks:
                        return await interaction.response.send_message("ℹ️ Cette liste est vide", ephemeral=True)

                    # Créez un deuxième menu déroulant pour sélectionner la tâche
                    task_select = Select(placeholder="Choisissez une tâche à modifier")
                    task_select.options = [discord.SelectOption(label=f"{task['id']}: {task['task']}") for task in tasks]

                    async def task_select_callback(interaction):
                        try:
                            selected_task_id = int(interaction.data["values"][0].split(":")[0])
                            selected_task = next(task for task in tasks if task["id"] == selected_task_id)

                            # Stockage de la liste ET de la tâche
                            selected_tasks[str(interaction.user.id)] = {
                                "list": selected_list,
                                "task_id": selected_task_id
                            }

                            # Créez un modal pour modifier la tâche
                            modal = Modal(title="Modifier la tâche")
                            modal.add_item(TextInput(
                                label="Nouvelle description",
                                placeholder=selected_task["task"],
                                default=selected_task["task"],
                                custom_id="new_task_description"
                            ))
                            modal.custom_id = "edit_task_modal"
                            await interaction.response.send_modal(modal)
                        except Exception as e:
                            self.log_error(e, "edit_task_select")
                            await self.send_error(interaction)

                    task_select.callback = task_select_callback
                    view = View()
                    view.add_item(task_select)

                    await interaction.response.send_message("Choisissez une tâche à modifier :", view=view, ephemeral=True)
                except Exception as e:
                    self.log_error(e, "edit_task_select")
                    await self.send_error(interaction)

            select.callback = select_callback
            view = View()
            view.add_item(select)

            await interaction.response.send_message("Choisissez une liste :", view=view, ephemeral=True)

        except Exception as e:
            self.log_error(e, "edit_task")
            await self.send_error(interaction)

    async def handle_edit_task_modal(self, interaction):
        """Traite la modification d'une tâche (version corrigée)"""
        try:
            user_id = str(interaction.user.id)
            data = selected_tasks.get(user_id)
            
            if not data:
                return await interaction.response.send_message("⚠️ Session expirée", ephemeral=True)
                
            list_name, task_id = data["list"], data["task_id"]
            new_description = interaction.data["components"][0]["components"][0]["value"].strip()

            if not new_description:
                return await interaction.response.send_message("❌ Description vide", ephemeral=True)

            # Trouve et met à jour la tâche
            for task in user_tasks[user_id][list_name]:
                if task["id"] == task_id:
                    task["task"] = new_description
                    break

            await interaction.response.send_message("✅ Tâche modifiée !", ephemeral=True)
            del selected_tasks[user_id]  # Nettoyage

        except Exception as e:
            self.log_error(e, "edit_task_modal")
            await self.send_error(interaction)
    # endregion

    # region Utilitaires
    def log_error(self, error, context):
        """Journalise les erreurs avec contexte"""
        print(f"\n⚠️ ERREUR dans {context} ⚠️")
        traceback.print_exc()
        print(f"Type: {type(error)}")
        print(f"Message: {str(error)}\n")

    async def send_error(self, interaction):
        """Envoie un message d'erreur générique"""
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("❌ Une erreur s'est produite", ephemeral=True)
        except Exception as e:
            print(f"Impossible d'envoyer le message d'erreur : {str(e)}")
    # endregion


async def setup(bot):
    await bot.add_cog(Tasks(bot))
