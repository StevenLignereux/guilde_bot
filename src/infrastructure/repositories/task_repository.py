from typing import List, Optional
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.task import Task, TaskList
from src.infrastructure.repositories.postgres_repository import PostgresRepository

# Configuration du logging
logger = logging.getLogger(__name__)

class TaskRepository(PostgresRepository[Task]):
    def __init__(self):
        super().__init__(Task)
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        try:
            return self.db.query(TaskList).filter(TaskList.user_discord_id == user_discord_id).all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des listes: {str(e)}")
            raise
    
    async def create_list(self, name: str, user_discord_id: str) -> TaskList:
        try:
            # Vérifier si une liste avec le même nom existe déjà pour cet utilisateur
            existing_list = self.db.query(TaskList).filter(
                TaskList.user_discord_id == user_discord_id,
                TaskList.name == name
            ).first()
            
            if existing_list:
                raise ValueError(f"Une liste nommée '{name}' existe déjà")
            
            task_list = TaskList(name=name, user_discord_id=user_discord_id)
            self.db.add(task_list)
            self.db.commit()
            self.db.refresh(task_list)
            return task_list
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            raise
    
    async def add_task(self, description: str, task_list_id: int) -> Task:
        try:
            # Vérifier si la liste existe
            task_list = self.db.query(TaskList).filter(TaskList.id == task_list_id).first()
            if not task_list:
                raise ValueError(f"La liste avec l'ID {task_list_id} n'existe pas")
                
            task = Task(description=description, task_list_id=task_list_id)
            self.db.add(task)
            self.db.commit()
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            raise
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.completed = not task.completed
                self.db.commit()
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du basculement de la tâche: {str(e)}")
            raise
        
    async def update_task_description(self, task_id: int, new_description: str) -> Task:
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")
            task.description = new_description
            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la description de la tâche: {str(e)}")
            raise

    async def delete_list(self, list_id: int) -> bool:
        """
        Supprime une liste de tâches et toutes ses tâches associées.
        
        Args:
            list_id: L'identifiant de la liste à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si la liste n'existe pas
        """
        try:
            task_list = self.db.query(TaskList).filter(TaskList.id == list_id).first()
            if not task_list:
                raise ValueError(f"La liste avec l'ID {list_id} n'existe pas")
            
            # Supprime d'abord toutes les tâches associées
            self.db.query(Task).filter(Task.task_list_id == list_id).delete()
            
            # Puis supprime la liste
            self.db.delete(task_list)
            self.db.commit()
            return True
            
        except ValueError as e:
            logger.error(f"Erreur lors de la suppression de la liste: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la liste: {str(e)}")
            return False 