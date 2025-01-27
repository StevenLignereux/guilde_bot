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
        options = []
        for task_list in task_lists:
            completed_tasks = sum(1 for task in task_list.tasks if task.completed)
            total_tasks = len(task_list.tasks)
            progress = f"[{completed_tasks}/{total_tasks}]"
            
            # Emoji basé sur le nom de la liste
            emoji = "📋"
            if "course" in task_list.name.lower():
                emoji = "🛒"
            elif "maison" in task_list.name.lower():
                emoji = "🏠"
            elif "travail" in task_list.name.lower():
                emoji = "💼"
            elif "urgent" in task_list.name.lower():
                emoji = "🚨"
            
            options.append(
                discord.SelectOption(
                    label=f"{task_list.name}",
                    description=f"{progress} • Créée le {task_list.created_at.strftime('%d/%m/%Y')}",
                    value=str(task_list.id),
                    emoji=emoji
                )
            )
        
        super().__init__(
            placeholder="📋 Sélectionnez une liste",
            min_values=1,
            max_values=1,
            options=options
        )
        self.task_lists = {str(tl.id): tl for tl in task_lists}

    async def callback(self, interaction: discord.Interaction):
        try:
            list_id = self.values[0]
            task_list = self.task_lists[list_id]
            
            if self.task_service:
                lists = await self.task_service.get_user_lists(str(interaction.user.id))
                task_list = next((lst for lst in lists if lst.id == int(list_id)), task_list)
            
            completed_tasks = sum(1 for task in task_list.tasks if task.completed)
            total_tasks = len(task_list.tasks)
            progress_bar = "▓" * completed_tasks + "░" * (total_tasks - completed_tasks)
            
            embed = discord.Embed(
                title=f"📋 {task_list.name}",
                description=f"Progression : {progress_bar} ({completed_tasks}/{total_tasks})",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Créée le",
                value=task_list.created_at.strftime("%d/%m/%Y à %H:%M"),
                inline=True
            )
            
            tasks_content = ""
            view = TaskListView()
            
            if task_list.tasks:
                for i, task in enumerate(task_list.tasks, 1):
                    status = "✅" if task.completed else "⬜"
                    description = f"~~{task.description}~~" if task.completed else task.description
                    tasks_content += f"{i}. {status} {description}\n\n"
                    view.add_item(TaskButton(task.id, task.completed, f"Marquer #{i}"))
                tasks_content = tasks_content.rstrip()
            else:
                tasks_content = "*Cette liste est vide*"
            
            embed.add_field(name="Tâches", value="\n" + tasks_content, inline=False)
            
            # Ajouter les boutons d'action
            view.add_item(AddTaskButton(task_list.id))
            view.add_item(DeleteCompletedButton(task_list.id))
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
            await interaction.response.defer()
            
            task_service = TaskService()
            view = MainMenuView(task_service)
            
            embed = discord.Embed(
                title="📋 Gestionnaire de tâches",
                description="Que souhaitez-vous faire ?",
                color=discord.Color.blue()
            )
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Erreur lors du retour au menu: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue !", ephemeral=True)

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
                
                if task_list and hasattr(task_list, 'name'):
                    embed = discord.Embed(
                        title="📋 Vos listes de tâches",
                        description=f"✅ Liste '{task_list.name}' créée avec succès !",
                        color=discord.Color.green()
                    )
                else:
                    await interaction.followup.send("❌ Erreur lors de la création de la liste", ephemeral=True)
                    return
                
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(f"❌ {message}", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la création de la liste !", ephemeral=True)

class TaskButton(ui.Button):
    def __init__(self, task_id: int, completed: bool, label: str):
        super().__init__(
            style=discord.ButtonStyle.success if not completed else discord.ButtonStyle.secondary,
            label=label,
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
                    completed_tasks = sum(1 for task in task_list.tasks if task.completed)
                    total_tasks = len(task_list.tasks)
                    progress_bar = "▓" * completed_tasks + "░" * (total_tasks - completed_tasks)
                    
                    embed = discord.Embed(
                        title=f"📋 {task_list.name}",
                        description=f"Progression : {progress_bar} ({completed_tasks}/{total_tasks})",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(
                        name="Créée le",
                        value=task_list.created_at.strftime("%d/%m/%Y à %H:%M"),
                        inline=True
                    )
                    
                    tasks_content = ""
                    view = TaskListView()
                    
                    for i, t in enumerate(task_list.tasks, 1):
                        status = "✅" if t.completed else "⬜"
                        description = f"~~{t.description}~~" if t.completed else t.description
                        tasks_content += f"{i}. {status} {description}\n\n"
                        view.add_item(TaskButton(t.id, t.completed, f"Marquer #{i}"))
                    
                    tasks_content = tasks_content.rstrip()
                    embed.add_field(name="Tâches", value="\n" + tasks_content, inline=False)
                    
                    # Ajouter les boutons d'action
                    view.add_item(AddTaskButton(task_list.id))
                    view.add_item(DeleteCompletedButton(task_list.id))
                    view.add_item(BackToMenuButton(lists))
                    
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
    def __init__(self, task_list_id: int):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="➕ Ajouter une tâche",
            custom_id=f"add_task_{task_list_id}"
        )
        self.task_list_id = task_list_id

    async def callback(self, interaction: discord.Interaction):
        modal = AddTaskModal(self.task_list_id)
        await interaction.response.send_modal(modal)

class AddTaskModal(ui.Modal, title="Ajouter une tâche"):
    description = ui.TextInput(
        label="Tâche à faire",
        placeholder="Décrivez la tâche à accomplir",
        min_length=1,
        max_length=100
    )

    def __init__(self, task_list_id: int):
        super().__init__()
        self.task_list_id = task_list_id
        self.task_service = TaskService()

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            if not self.task_service:
                self.task_service = TaskService()
            task = await self.task_service.add_task(str(self.description), self.task_list_id)
            
            # Récupérer la liste mise à jour
            lists = await self.task_service.get_user_lists(str(interaction.user.id))
            task_list = next((lst for lst in lists if lst.id == self.task_list_id), None)
            
            if task_list:
                completed_tasks = sum(1 for task in task_list.tasks if task.completed)
                total_tasks = len(task_list.tasks)
                progress_bar = "▓" * completed_tasks + "░" * (total_tasks - completed_tasks)
                
                embed = discord.Embed(
                    title=f"📋 {task_list.name}",
                    description=f"✅ Tâche ajoutée avec succès !\nProgression : {progress_bar} ({completed_tasks}/{total_tasks})",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="Créée le",
                    value=task_list.created_at.strftime("%d/%m/%Y à %H:%M"),
                    inline=True
                )
                
                tasks_content = ""
                view = TaskListView()
                
                for i, t in enumerate(task_list.tasks, 1):
                    status = "✅" if t.completed else "⬜"
                    description = f"~~{t.description}~~" if t.completed else t.description
                    tasks_content += f"{i}. {status} {description}\n\n"
                    view.add_item(TaskButton(t.id, t.completed, f"Marquer #{i}"))
                
                tasks_content = tasks_content.rstrip()
                embed.add_field(name="Tâches", value="\n" + tasks_content, inline=False)
                
                # Ajouter les boutons d'action
                view.add_item(AddTaskButton(task_list.id))
                view.add_item(DeleteCompletedButton(task_list.id))
                view.add_item(BackToMenuButton(lists))
                
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send("❌ Une erreur est survenue lors de l'ajout de la tâche !", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'ajout de la tâche !", ephemeral=True)

class DeleteCompletedButton(ui.Button):
    def __init__(self, task_list_id: int):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="🗑️ Supprimer les tâches complétées",
            custom_id=f"delete_completed_{task_list_id}"
        )
        self.task_list_id = task_list_id

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            
            task_service = TaskService()
            success = await task_service.delete_completed_tasks(self.task_list_id)
            
            if success:
                # Récupérer la liste mise à jour
                lists = await task_service.get_user_lists(str(interaction.user.id))
                task_list = next((lst for lst in lists if lst.id == self.task_list_id), None)
                
                if task_list:
                    completed_tasks = sum(1 for task in task_list.tasks if task.completed)
                    total_tasks = len(task_list.tasks)
                    progress_bar = "▓" * completed_tasks + "░" * (total_tasks - completed_tasks)
                    
                    embed = discord.Embed(
                        title=f"📋 {task_list.name}",
                        description=f"✅ Tâches complétées supprimées avec succès !\nProgression : {progress_bar} ({completed_tasks}/{total_tasks})",
                        color=discord.Color.green()
                    )
                    
                    embed.add_field(
                        name="Créée le",
                        value=task_list.created_at.strftime("%d/%m/%Y à %H:%M"),
                        inline=True
                    )
                    
                    tasks_content = ""
                    view = TaskListView()
                    
                    for i, t in enumerate(task_list.tasks, 1):
                        status = "✅" if t.completed else "⬜"
                        description = f"~~{t.description}~~" if t.completed else t.description
                        tasks_content += f"{i}. {status} {description}\n\n"
                        view.add_item(TaskButton(t.id, t.completed, f"Marquer #{i}"))
                    
                    tasks_content = tasks_content.rstrip()
                    embed.add_field(name="Tâches", value="\n" + tasks_content, inline=False)
                    
                    # Ajouter les boutons d'action
                    view.add_item(AddTaskButton(task_list.id))
                    view.add_item(DeleteCompletedButton(task_list.id))
                    view.add_item(BackToMenuButton(lists))
                    
                    await interaction.edit_original_response(embed=embed, view=view)
                else:
                    await interaction.followup.send("❌ Liste non trouvée !", ephemeral=True)
            else:
                await interaction.followup.send("❌ La liste n'a pas été trouvée ou aucune tâche complétée à supprimer !", ephemeral=True)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des tâches complétées: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la suppression des tâches complétées !", ephemeral=True)

class MainMenuView(ui.View):
    def __init__(self, task_service: TaskService):
        super().__init__(timeout=None)
        self.add_item(ShowListsButton(task_service))
        self.add_item(CreateListButton(task_service))

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
            
            if not self.task_service:
                self.task_service = TaskService()
                
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
            if not self.task_service:
                self.task_service = TaskService()
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
            if not self.task_service:
                self.task_service = TaskService()
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
            if not self.task_service:
                self.task_service = TaskService()
            success = await self.task_service.delete_list(list_id)
            if success:
                await interaction.followup.send("✅ Liste supprimée avec succès !")
            else:
                await interaction.followup.send("❌ La liste n'a pas été trouvée !")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la liste: {str(e)}")
            await interaction.followup.send("❌ Une erreur est survenue lors de la suppression de la liste !") 