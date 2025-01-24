from typing import List, Optional
import logging
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
        except SQLAlchemyError as e:
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
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            raise
    
    async def add_task(self, description: str, task_list_id: int) -> Task:
        # Vérifier si la liste existe
        task_list = self.db.query(TaskList).filter(TaskList.id == task_list_id).first()
        if not task_list:
            raise ValueError(f"La liste avec l'ID {task_list_id} n'existe pas")
            
        task = Task(description=description, task_list_id=task_list_id)
        self.db.add(task)
        self.db.commit()
        return task
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.completed = not task.completed
            self.db.commit()
        return task
        
    async def update_task_description(self, task_id: int, new_description: str) -> Optional[Task]:
        """Met à jour la description d'une tâche."""
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.description = new_description
                self.db.commit()
                self.db.refresh(task)
            return task
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la tâche: {str(e)}")
            raise 