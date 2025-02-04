from typing import List, Optional, Tuple
import logging
from src.infrastructure.repositories.task_repository import TaskRepository
from src.domain.entities.task import Task, TaskList
from src.infrastructure.config.database import init_db, async_session
from src.config.config import load_config
from src.infrastructure.config.db_state import DatabaseState
from src.domain.exceptions import TaskNotFoundError, InvalidTaskStateError, DatabaseConnectionError
from sqlalchemy.sql import select
from sqlalchemy.orm import selectinload
from src.infrastructure.config.database import get_session

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskService:
    """
    Service de gestion des tâches.
    
    Gère toutes les opérations liées aux tâches et listes de tâches :
    création, modification, suppression et recherche.
    
    Attributes:
        repository (TaskRepository): Repository pour l'accès aux données
        _initialized (bool): État d'initialisation du service
    """
    def __init__(self):
        self._initialized = True
        self.repository = TaskRepository()
        logger.debug("TaskService initialisé")
    
    async def _ensure_initialized(self):
        if not self._initialized:
            config = load_config()
            await init_db(config.database)
            # S'assurer que la session est disponible
            await DatabaseState.ensure_initialized()
            self._initialized = True
    
    async def create_list(self, user_discord_id: str, name: str) -> Tuple[bool, str, Optional[TaskList]]:
        """Crée une nouvelle liste de tâches"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                task_list = TaskList(
                    name=name,
                    user_discord_id=user_discord_id,
                    tasks=[]  # Initialisation explicite de la liste des tâches
                )
                session.add(task_list)
                await session.commit()
                await session.refresh(task_list)
                
                # Requête explicite pour charger la liste avec ses tâches
                query = select(TaskList).filter_by(id=task_list.id).options(
                    selectinload(TaskList.tasks)
                )
                result = await session.execute(query)
                task_list = result.scalar_one()
                
                return True, "Liste créée avec succès", task_list
        except Exception as e:
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            return False, "Erreur lors de la création de la liste", None
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        """Récupère toutes les listes d'un utilisateur"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                # Utiliser selectinload pour charger les tâches en même temps
                query = select(TaskList).filter_by(user_discord_id=user_discord_id).options(
                    selectinload(TaskList.tasks)
                )
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des listes: {str(e)}")
            return []
    
    async def add_task(self, description: str, task_list_id: int) -> Optional[Task]:
        """Ajoute une tâche à une liste"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                task = Task(
                    description=description,
                    task_list_id=task_list_id
                )
                session.add(task)
                await session.commit()
                await session.refresh(task)
                return task
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            return None
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        """Change l'état d'une tâche (complétée/non complétée)"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                query = select(Task).filter_by(id=task_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
                
                if task:
                    task.completed = not task.completed
                    await session.commit()
                    await session.refresh(task)
                    
                return task
        except Exception as e:
            logger.error(f"Erreur lors du changement d'état de la tâche: {str(e)}")
            return None
    
    async def update_task_description(self, task_id: int, new_description: str) -> Optional[Task]:
        """Met à jour la description d'une tâche"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                query = select(Task).filter_by(id=task_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
                
                if task:
                    task.description = new_description
                    await session.commit()
                    await session.refresh(task)
                    
                return task
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la description: {str(e)}")
            return None
    
    async def delete_task(self, task_id: int) -> bool:
        """Supprime une tâche"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                query = select(Task).filter_by(id=task_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
                
                if task:
                    await session.delete(task)
                    await session.commit()
                    return True
                    
                return False
        except Exception as e:
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
        """Supprime une liste et toutes ses tâches"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                query = select(TaskList).filter_by(id=list_id)
                result = await session.execute(query)
                task_list = result.scalar_one_or_none()
                
                if task_list:
                    await session.delete(task_list)
                    await session.commit()
                    return True
                    
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la liste: {str(e)}")
            return False

    async def delete_completed_tasks(self, task_list_id: int) -> bool:
        try:
            task_list = await self.repository.get_list(task_list_id)
            if not task_list:
                return False
            
            completed_tasks = [task for task in task_list.tasks if task.completed]
            if not completed_tasks:
                return False
            
            all_deleted = True
            for task in completed_tasks:
                success = await self.repository.delete_task(task.id)
                if not success:
                    all_deleted = False
            
            return all_deleted
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
        """Récupère une liste par son ID"""
        await self._ensure_initialized()
        try:
            async with get_session() as session:
                query = select(TaskList).filter_by(id=list_id).options(
                    selectinload(TaskList.tasks)
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste {list_id}: {str(e)}")
            return None

    async def get_all_tasks(self):
        try:
            return await self.repository.get_all()
        except Exception as e:
            logger.error(f"Erreur dans get_all_tasks: {str(e)}")
            raise

    async def create_task(self, data):
        try:
            return await self.repository.add(data)
        except Exception as e:
            logger.error(f"Erreur dans create_task: {str(e)}")
            raise 