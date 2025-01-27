from typing import List, Optional, Tuple
import logging
from src.infrastructure.repositories.task_repository import TaskRepository
from src.domain.entities.task import Task, TaskList
from src.infrastructure.config.database import init_db, async_session
from src.config.config import load_config
from src.infrastructure.config.db_state import DatabaseState
from src.domain.exceptions import TaskNotFoundError, InvalidTaskStateError, DatabaseConnectionError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self, repository: Optional[TaskRepository] = None):
        self.repository = repository if repository is not None else TaskRepository()
        self._initialized = False
    
    async def _ensure_initialized(self):
        if not self._initialized:
            config = load_config()
            await init_db(config.database)
            # S'assurer que la session est disponible
            await DatabaseState.ensure_initialized()
            self._initialized = True
    
    async def create_list(self, user_discord_id: str, name: str) -> Tuple[bool, str, Optional[TaskList]]:
        try:
            await self._ensure_initialized()
            
            if not name or len(name.strip()) == 0:
                return False, "Le nom de la liste ne peut pas être vide", None
                
            if len(name) > 100:  # Limite raisonnable pour un nom de liste
                return False, "Le nom de la liste est trop long (max 100 caractères)", None
            
            task_list = await self.repository.create_list(user_discord_id, name.strip())
            return True, "Liste créée avec succès", task_list
            
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de la liste: {str(e)}")
            return False, "Une erreur est survenue lors de la création de la liste", None
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        await self._ensure_initialized()
        return await self.repository.get_user_lists(user_discord_id)
    
    async def add_task(self, description: str, task_list_id: int) -> Optional[Task]:
        """
        Ajoute une nouvelle tâche à une liste.
        
        Args:
            description: La description de la tâche
            task_list_id: L'identifiant de la liste à laquelle ajouter la tâche
            
        Returns:
            Task: La tâche créée
            
        Raises:
            ValueError: Si la description est vide ou si la liste n'existe pas
        """
        try:
            if not description or len(description.strip()) == 0:
                raise ValueError("La description de la tâche ne peut pas être vide")
                
            if len(description) > 500:  # Limite raisonnable pour une description
                raise ValueError("La description de la tâche est trop longue (max 500 caractères)")
            
            return await self.repository.add_task(description.strip(), task_list_id)
            
        except ValueError as e:
            logger.error(f"Erreur de validation lors de l'ajout de la tâche: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'ajout de la tâche: {str(e)}")
            raise
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        return await self.repository.toggle_task(task_id)
    
    async def update_task_description(self, task_id: int, new_description: str) -> Optional[Task]:
        """Met à jour la description d'une tâche."""
        return await self.repository.update_task_description(task_id, new_description)
    
    async def delete_task(self, task_id: int) -> bool:
        """
        Supprime une tâche spécifique.
        
        Args:
            task_id: L'identifiant de la tâche à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
            
        Raises:
            ValueError: Si la tâche n'existe pas
        """
        try:
            result = await self.repository.delete_task(task_id)
            return bool(result)  # Convertit explicitement en bool
        except ValueError as e:
            logger.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
            return False
    
    async def check_database(self):
        """Vérifie l'état de la base de données."""
        try:
            test_list = await self.repository.create_list("__test__", "__test__")
            if test_list is None:
                return False, "Erreur de base de données : impossible de créer une liste de test"
            
            try:
                async with self.repository._get_session() as session:
                    await session.delete(test_list)
                    await session.commit()
            except Exception as e:
                return False, f"Erreur de base de données : {str(e)}"
                
            return True, "Base de données opérationnelle"
        except Exception as e:
            return False, f"Erreur de base de données : {str(e)}"

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
            await self._ensure_initialized()
            result = await self.repository.delete_list(list_id)
            return bool(result)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la liste {list_id}: {str(e)}")
            return False

    async def delete_completed_tasks(self, task_list_id: int) -> bool:
        try:
            task_list = await self.repository.get_list(task_list_id)
            if not task_list:
                return False
            
            completed_tasks = [task for task in task_list.tasks if task.completed]
            if not completed_tasks:
                return False
            
            for task in completed_tasks:
                await self.repository.delete_task(task.id)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des tâches complétées: {str(e)}")
            return False

    async def complete_task(self, task_id: str) -> Task:
        try:
            return await self.repository.update_task_status(task_id, "completed")
        except TaskNotFoundError as e:
            logger.warning(f"Tentative de compléter une tâche inexistante: {e.task_id}")
            raise
        except InvalidTaskStateError as e:
            logger.warning(
                f"Tentative de transition invalide de '{e.current_state}' vers '{e.attempted_state}'"
            )
            raise
        except DatabaseConnectionError as e:
            logger.error(f"Problème de base de données lors de la complétion de la tâche: {str(e)}")
            raise

    async def get_list(self, list_id: int) -> Optional[TaskList]:
        try:
            return await self.repository.get_list_by_id(list_id)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste {list_id}: {str(e)}")
            return None 