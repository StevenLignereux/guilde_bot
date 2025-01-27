import logging
from typing import Optional, List
import discord
from discord import app_commands, ui
from src.infrastructure.commands.base import BaseCommand
from src.application.services.task_service import TaskService
from src.domain.entities.task import Task, TaskList

logger = logging.getLogger(__name__)

class TaskListSelect(ui.Select):
    def __init__(self, task_lists: List[TaskList], task_service: Optional[TaskService] = None):
        self.task_service = task_service
        options = [
            discord.SelectOption(
                label=f"{task_list.name}",
                description=f"{len(task_list.tasks)} tâches",
                value=str(task_list.id)
            ) for task_list in task_lists
        ]
        super().__init__(
            placeholder="Choisissez une liste à afficher",
            min_values=1,
            max_values=1,
            options=options
        )
        self.task_lists = {str(tl.id): tl for tl in task_lists}

    async def refresh_lists(self, interaction: discord.Interaction):
        if self.task_service:
            lists = await self.task_service.get_user_lists(str(interaction.user.id))
            options = [
                discord.SelectOption(
                    label=f"{task_list.name}",
                    description=f"{len(task_list.tasks)} tâches",
                    value=str(task_list.id)
                ) for task_list in lists
            ]
            self.options = options
            self.task_lists = {str(tl.id): tl for tl in lists}
            return lists
        return None

    async def callback(self, interaction: discord.Interaction):
        try:
            list_id = self.values[0]
            task_list = self.task_lists[list_id]
            
            # Si on a un task_service, rafraîchir la liste
            if self.task_service:
                lists = await self.task_service.get_user_lists(str(interaction.user.id))
                task_list = next((lst for lst in lists if lst.id == int(list_id)), task_list)
            
            embed = discord.Embed(
                title=f"📋 {task_list.name}",
                color=discord.Color.blue()
            )
            
            tasks_content = ""
            view = TaskListView()
            
            if task_list.tasks:
                for task in task_list.tasks:
                    status = "✅" if task.completed else "⬜"
                    description = f"~~{task.description}~~" if task.completed else task.description
                    tasks_content += f"{status} {description}\n"
                    view.add_item(TaskButton(task.id, task.completed))
            else:
                tasks_content = "*Cette liste est vide*"
            
            embed.add_field(name="Tâches", value=tasks_content, inline=False)
            
            # Ajouter un bouton pour retourner au menu principal
            view.add_item(BackToMenuButton(list(self.task_lists.values())))
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la liste: {str(e)}")
            await interaction.response.send_message("❌ Une erreur est survenue !", ephemeral=True)

class BackToMenuButton(ui.Button):
    def __init__(self, task_lists: List[TaskList]):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="↩️ Retour au menu",
            custom_id="back_to_menu"
        )
        self.task_lists = task_lists

    async def callback(self, interaction: discord.Interaction):
        try:
            view = discord.ui.View(timeout=None)
            view.add_item(TaskListSelect(self.task_lists))
            
            embed = discord.Embed(
                title="📋 Vos listes de tâches",
                description="Sélectionnez une liste pour voir son contenu",
                color=discord.Color.blue()
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors du retour au menu: {str(e)}")
            await interaction.response.send_message("❌ Une erreur est survenue !", ephemeral=True)

class ShowListsButton(ui.Button):
    def __init__(self, task_service: TaskService):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="📋 Afficher les listes",
            custom_id="show_lists"
        )
        self.task_service = task_service

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            lists = await self.task_service.get_user_lists(str(interaction.user.id))
            if not lists:
                await interaction.followup.send("Vous n'avez pas encore de liste de tâches !", ephemeral=True)
                return
            
            view = discord.ui.View(timeout=None)
            view.add_item(TaskListSelect(lists, self.task_service))
            
            embed = discord.Embed(
                title="📋 Vos listes de tâches",
                description="Sélectionnez une liste pour voir son contenu",
                color=discord.Color.blue()
            )
            
            # Afficher les listes disponibles
            lists_content = ""
            for lst in lists:
                lists_content += f"• {lst.name} ({len(lst.tasks)} tâches)\n"
            
            if lists_content:
                embed.add_field(name="Listes disponibles", value=lists_content, inline=False)
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des listes: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue !", ephemeral=True)

class CreateListButton(ui.Button):
    def __init__(self, task_service: TaskService):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="➕ Créer une liste",
            custom_id="create_list"
        )
        self.task_service = task_service

    async def callback(self, interaction: discord.Interaction):
        modal = CreateListModal(self.task_service)
        await interaction.response.send_modal(modal)

class ListDisplayView(ui.View):
    def __init__(self, task_service: TaskService, lists: List[TaskList]):
        super().__init__(timeout=None)
        self.task_service = task_service
        self.lists = lists
        self.add_item(TaskListSelect(lists))

class CreateListModal(ui.Modal, title="Créer une nouvelle liste"):
    name = ui.TextInput(
        label="Nom de la liste",
        placeholder="Par exemple : Courses, Tâches ménagères, etc.",
        min_length=1,
        max_length=100
    )

    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            success, message, task_list = await self.task_service.create_list(str(interaction.user.id), str(self.name))
            
            if success:
                lists = await self.task_service.get_user_lists(str(interaction.user.id))
                view = discord.ui.View(timeout=None)
                select = TaskListSelect(lists, self.task_service)
                view.add_item(select)
                
                embed = discord.Embed(
                    title="📋 Vos listes de tâches",
                    description=f"✅ Liste '{task_list.name}' créée avec succès !",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(f"❌ {message}", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la création de la liste !", ephemeral=True)

class TaskButton(ui.Button):
    def __init__(self, task_id: int, completed: bool):
        super().__init__(
            style=discord.ButtonStyle.success if completed else discord.ButtonStyle.secondary,
            label="✓" if completed else "○",
            custom_id=f"task_{task_id}"
        )
        self.task_id = task_id
        self.completed = completed

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            task_service = TaskService()
            task = await task_service.toggle_task(self.task_id)
            
            if task:
                lists = await task_service.get_user_lists(str(interaction.user.id))
                task_list = next((lst for lst in lists if any(t.id == task.id for t in lst.tasks)), None)
                
                if task_list:
                    embed = discord.Embed(
                        title=f"📋 {task_list.name}",
                        description=f"ID: {task_list.id}",
                        color=discord.Color.blue()
                    )
                    
                    tasks_content = ""
                    view = TaskListView()
                    for t in task_list.tasks:
                        status = "✅" if t.completed else "❌"
                        description = f"~~{t.description}~~" if t.completed else t.description
                        tasks_content += f"{status} {description} (ID: {t.id})\n"
                        view.add_item(TaskButton(t.id, t.completed))
                    
                    embed.add_field(name="Tâches", value=tasks_content, inline=False)
                    await interaction.edit_original_response(embed=embed, view=view)
                else:
                    await interaction.followup.send("❌ Liste non trouvée !", ephemeral=True)
            else:
                await interaction.followup.send("❌ La tâche n'a pas été trouvée !", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la tâche: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue !", ephemeral=True)

class TaskListView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class AddTaskButton(ui.Button):
    def __init__(self, task_service: TaskService):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="➕ Ajouter une tâche",
            custom_id="add_task"
        )
        self.task_service = task_service

    async def callback(self, interaction: discord.Interaction):
        modal = AddTaskModal(self.task_service)
        await interaction.response.send_modal(modal)

class AddTaskModal(ui.Modal, title="Ajouter une tâche"):
    list_name = ui.TextInput(
        label="Nom de la liste",
        placeholder="Dans quelle liste voulez-vous ajouter la tâche ?",
        min_length=1,
        max_length=100
    )
    description = ui.TextInput(
        label="Tâche à faire",
        placeholder="Décrivez la tâche à accomplir",
        min_length=1,
        max_length=100
    )

    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            # Trouver la liste par son nom
            lists = await self.task_service.get_user_lists(str(interaction.user.id))
            task_list = next((lst for lst in lists if lst.name.lower() == str(self.list_name).lower()), None)
            
            if not task_list:
                await interaction.followup.send(f"❌ Liste '{self.list_name}' introuvable. Vérifiez le nom de la liste.", ephemeral=True)
                return
            
            task = await self.task_service.add_task(str(self.description), task_list.id)
            
            # Afficher la liste mise à jour
            embed = discord.Embed(
                title=f"📋 {task_list.name}",
                description="✅ Tâche ajoutée avec succès !",
                color=discord.Color.green()
            )
            
            tasks_content = ""
            view = TaskListView()
            
            for t in task_list.tasks:
                status = "✅" if t.completed else "⬜"
                description = f"~~{t.description}~~" if t.completed else t.description
                tasks_content += f"{status} {description}\n"
                view.add_item(TaskButton(t.id, t.completed))
            
            embed.add_field(name="Tâches", value=tasks_content, inline=False)
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'ajout de la tâche !")

class MainMenuView(ui.View):
    def __init__(self, task_service: TaskService):
        super().__init__(timeout=None)
        self.add_item(ShowListsButton(task_service))
        self.add_item(CreateListButton(task_service))
        self.add_item(AddTaskButton(task_service))

class TaskCommands(BaseCommand):
    """Commandes de gestion des tâches"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.task_service = None
        
    async def setup(self) -> None:
        """Configure les commandes pour le bot"""
        # Initialiser le service après que la base de données soit prête
        self.task_service = TaskService()
        
        # Ajouter les commandes directement au bot
        self.bot.tree.add_command(self.list_tasks)
        self.bot.tree.add_command(self.add_task)
        self.bot.tree.add_command(self.delete_task)
        self.bot.tree.add_command(self.delete_list)
        
        logger.info("Commandes de tâches configurées")

    @app_commands.command(
        name="tasks",
        description="Gérer vos listes de tâches"
    )
    async def list_tasks(
        self,
        interaction: discord.Interaction
    ):
        """Affiche le menu principal de gestion des tâches"""
        try:
            await interaction.response.defer()
            
            embed = discord.Embed(
                title="📋 Gestionnaire de tâches",
                description="Que souhaitez-vous faire ?",
                color=discord.Color.blue()
            )
            
            view = MainMenuView(self.task_service)
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du menu: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue !")
    
    @app_commands.command(
        name="add_task",
        description="Ajoute une tâche à une liste"
    )
    async def add_task(
        self,
        interaction: discord.Interaction,
        list_id: int,
        description: str
    ):
        """Ajoute une tâche à une liste"""
        try:
            await interaction.response.defer()
            task = await self.task_service.add_task(description, list_id)
            await interaction.followup.send(f"✅ Tâche ajoutée avec succès à la liste {list_id} !")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'ajout de la tâche !")
    
    @app_commands.command(
        name="delete_task",
        description="Supprime une tâche"
    )
    async def delete_task(
        self,
        interaction: discord.Interaction,
        task_id: int
    ):
        """Supprime une tâche"""
        try:
            await interaction.response.defer()
            success = await self.task_service.delete_task(task_id)
            if success:
                await interaction.followup.send("✅ Tâche supprimée avec succès !")
            else:
                await interaction.followup.send("❌ La tâche n'a pas été trouvée !")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la suppression de la tâche !")
    
    @app_commands.command(
        name="delete_list",
        description="Supprime une liste de tâches"
    )
    async def delete_list(
        self,
        interaction: discord.Interaction,
        list_id: int
    ):
        """Supprime une liste de tâches"""
        try:
            await interaction.response.defer()
            success = await self.task_service.delete_list(list_id)
            if success:
                await interaction.followup.send("✅ Liste supprimée avec succès !")
            else:
                await interaction.followup.send("❌ La liste n'a pas été trouvée !")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la liste: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la suppression de la liste !") 