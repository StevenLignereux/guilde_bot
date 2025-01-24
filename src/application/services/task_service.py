from typing import List, Optional, Tuple
import logging
from src.infrastructure.repositories.task_repository import TaskRepository
from src.domain.entities.task import Task, TaskList

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self):
        self.repository = TaskRepository()
    
    async def create_list(self, name: str, user_discord_id: str) -> Tuple[bool, str, Optional[TaskList]]:
        try:
            if not name or len(name.strip()) == 0:
                return False, "Le nom de la liste ne peut pas être vide", None
                
            if len(name) > 100:  # Limite raisonnable pour un nom de liste
                return False, "Le nom de la liste est trop long (max 100 caractères)", None
            
            task_list = await self.repository.create_list(name.strip(), user_discord_id)
            return True, "Liste créée avec succès", task_list
            
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de la liste: {str(e)}")
            return False, "Une erreur est survenue lors de la création de la liste", None
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        return await self.repository.get_user_lists(user_discord_id)
    
    async def add_task(self, description: str, task_list_id: int) -> Task:
        return await self.repository.add_task(description, task_list_id)
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        return await self.repository.toggle_task(task_id)
    
    async def update_task_description(self, task_id: int, new_description: str) -> Optional[Task]:
        """Met à jour la description d'une tâche."""
        return await self.repository.update_task_description(task_id, new_description)
    
    async def check_database(self):
        """Vérifie l'état de la base de données."""
        try:
            test_list = await self.repository.create_list("__test__", "__test__")
            if test_list is None:
                return False, "Erreur de base de données : impossible de créer une liste de test"
            
            await self.repository.db.delete(test_list)
            await self.repository.db.commit()
            return True, "Base de données opérationnelle"
        except Exception as e:
            return False, f"Erreur de base de données : {str(e)}" 