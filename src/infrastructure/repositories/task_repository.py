from typing import List, Optional
import logging
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.domain.entities.task import Task, TaskList
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.infrastructure.config.database import get_session

# Configuration du logging
logger = logging.getLogger(__name__)

class TaskRepository(PostgresRepository[Task]):
    def __init__(self, db: Optional[AsyncSession] = None):
        super().__init__(Task)
        self._db = db
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        session = await get_session()
        try:
            query = select(TaskList).options(
                joinedload(TaskList.tasks)
            ).filter(TaskList.user_discord_id == user_discord_id)
            result = await session.execute(query)
            return result.unique().scalars().all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des listes: {str(e)}")
            raise
        finally:
            await session.close()
    
    async def create_list(self, user_discord_id: str, name: str) -> TaskList:
        session = await get_session()
        try:
            task_list = TaskList(
                name=name,
                user_discord_id=user_discord_id,
                created_at=datetime.now(UTC)
            )
            session.add(task_list)
            await session.commit()
            await session.refresh(task_list)
            return task_list
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors de la création de la liste: {str(e)}")
            raise
        finally:
            await session.close()
    
    async def add_task(self, description: str, task_list_id: int) -> Task:
        session = await get_session()
        try:
            task = Task(description=description, task_list_id=task_list_id)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors de l'ajout de la tâche: {str(e)}")
            raise
        finally:
            await session.close()
    
    async def toggle_task(self, task_id: int) -> Optional[Task]:
        session = await get_session()
        try:
            query = select(Task).filter(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task:
                task.completed = not task.completed
                await session.commit()
                await session.refresh(task)
            return task
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors du basculement de la tâche: {str(e)}")
            raise
        finally:
            await session.close()
    
    async def update_task_description(self, task_id: int, new_description: str) -> Task:
        async with self._get_session() as session:
            try:
                query = select(Task).filter(Task.id == task_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
                
                if not task:
                    raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")
                
                task.description = new_description
                await session.commit()
                await session.refresh(task)
                return task
            except Exception as e:
                await session.rollback()
                logger.error(f"Erreur lors de la mise à jour de la description de la tâche: {str(e)}")
                raise

    async def delete_task(self, task_id: int) -> bool:
        session = await get_session()
        try:
            query = select(Task).filter(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if not task:
                raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")
            
            await session.delete(task)
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors de la suppression de la tâche: {str(e)}")
            raise
        finally:
            await session.close()

    async def delete_list(self, list_id: int) -> bool:
        """Supprime une liste et toutes ses tâches associées"""
        session = await get_session()
        try:
            # Récupérer la liste
            query = select(TaskList).filter(TaskList.id == list_id)
            result = await session.execute(query)
            task_list = result.scalar_one_or_none()
            
            if not task_list:
                logger.warning(f"Tentative de suppression d'une liste inexistante (ID: {list_id})")
                return False
            
            # Supprimer la liste (les tâches seront supprimées automatiquement grâce à cascade="all, delete-orphan")
            await session.delete(task_list)
            await session.commit()
            logger.info(f"Liste supprimée avec succès (ID: {list_id})")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors de la suppression de la liste {list_id}: {str(e)}")
            raise
        finally:
            await session.close()

    async def get_list(self, list_id: int) -> Optional[TaskList]:
        session = await get_session()
        try:
            query = select(TaskList).options(
                joinedload(TaskList.tasks)
            ).filter(TaskList.id == list_id)
            result = await session.execute(query)
            return result.unique().scalar_one_or_none()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste: {str(e)}")
            raise
        finally:
            await session.close()