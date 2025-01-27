from typing import List, Optional
import logging
from datetime import datetime, UTC
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from src.domain.entities.task import Task, TaskList
from src.infrastructure.repositories.postgres_repository import PostgresRepository
from src.infrastructure.config.database import get_session
from src.domain.exceptions import TaskNotFoundError, DatabaseConnectionError, InvalidTaskStateError
from sqlalchemy.exc import SQLAlchemyError

# Configuration du logging
logger = logging.getLogger(__name__)

class TaskRepository(PostgresRepository[Task]):
    def __init__(self, db: AsyncSession | None = None):
        super().__init__(Task)
        self._db = db
    
    async def get_user_lists(self, user_discord_id: str) -> List[TaskList]:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(TaskList).where(TaskList.user_discord_id == user_discord_id)
            result = await session.execute(query)
            tasks = list(result.scalars().all())
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Erreur lors de la récupération des listes pour l'utilisateur {user_discord_id}: {str(e)}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def create_list(self, name: str, user_discord_id: str) -> TaskList:
        session = self._db if self._db is not None else await get_session()
        try:
            # Vérifier si une liste avec le même nom existe déjà
            query = select(TaskList).where(
                and_(
                    TaskList.name == name,
                    TaskList.user_discord_id == user_discord_id
                )
            )
            result = await session.execute(query)
            existing_list = result.scalar_one_or_none()
            
            if existing_list is not None:
                raise ValueError(f"Une liste avec le nom '{name}' existe déjà")

            task_list = TaskList(name=name, user_discord_id=user_discord_id)
            session.add(task_list)
            await session.commit()
            await session.refresh(task_list)
            return task_list
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors de la création de la liste {name}: {e}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def add_task(self, description: str, list_id: int) -> Task:
        session = self._db if self._db is not None else await get_session()
        try:
            # Vérifier si la liste existe
            query = select(TaskList).where(TaskList.id == list_id)
            result = await session.execute(query)
            task_list = result.scalar_one_or_none()
            
            if task_list is None:
                raise ValueError(f"La liste avec l'ID {list_id} n'existe pas")

            task = Task(description=description, task_list_id=list_id)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors de l'ajout de la tâche à la liste {list_id}: {e}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def toggle_task(self, task_id: int) -> Task | None:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(Task).where(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()

            if task is None:
                raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")

            task.completed = not task.completed
            await session.commit()
            await session.refresh(task)
            return task
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors du basculement de la tâche {task_id}: {str(e)}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def update_task_description(self, task_id: int, new_description: str) -> Task | None:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(Task).where(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()

            if task is None:
                raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")

            task.description = new_description
            await session.commit()
            await session.refresh(task)
            return task
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors de la mise à jour de la description de la tâche {task_id}: {str(e)}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def delete_list(self, list_id: int) -> None:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(TaskList).where(TaskList.id == list_id)
            result = await session.execute(query)
            task_list = result.scalar_one_or_none()

            if task_list is None:
                raise ValueError(f"La liste avec l'ID {list_id} n'existe pas")

            tasks_query = select(Task).where(Task.task_list_id == list_id)
            tasks_result = await session.execute(tasks_query)
            tasks = tasks_result.scalars().all()

            for task in tasks:
                await session.delete(task)

            await session.delete(task_list)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors de la suppression de la liste {list_id}: {str(e)}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()
    
    async def delete_task(self, task_id: int) -> None:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(Task).where(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task is None:
                raise ValueError(f"La tâche avec l'ID {task_id} n'existe pas")

            await session.delete(task)
            await session.commit()
        except SQLAlchemyError as e:
            if session is not None:
                await session.rollback()
            logger.error(f"Erreur lors de la suppression de la tâche {task_id}: {e}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()

    async def get_list(self, list_id: int) -> Optional[TaskList]:
        session = self._db if self._db is not None else await get_session()
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
            if self._db is None and session is not None:
                await session.close()

    async def get_task_by_id(self, task_id: str) -> Task:
        session = self._db if self._db is not None else await get_session()
        try:
            query = select(Task).filter(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task is None:
                raise TaskNotFoundError(task_id)
                
            return task
            
        except SQLAlchemyError as e:
            logger.error(f"Erreur base de données: {str(e)}")
            raise DatabaseConnectionError(str(e))
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            raise
        finally:
            if self._db is None and session is not None:
                await session.close()

    async def update_task_status(self, task_id: str, new_status: str) -> Task:
        session = self._db if self._db is not None else await get_session()
        try:
            task = await self.get_task_by_id(task_id)
            
            if not task.can_transition_to(new_status):
                raise InvalidTaskStateError(task.status, new_status)
            
            task.status = new_status
            await session.commit()
            return task
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Erreur lors de la mise à jour du statut de la tâche {task_id}: {str(e)}")
            raise DatabaseConnectionError(str(e))
        finally:
            if self._db is None and session is not None:
                await session.close()

    async def get_list_by_id(self, list_id: int) -> Optional[TaskList]:
        async with self._get_session() as session:
            try:
                query = select(TaskList).options(
                    joinedload(TaskList.tasks)
                ).filter(TaskList.id == list_id)
                result = await session.execute(query)
                return result.unique().scalar_one_or_none()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la liste {list_id}: {str(e)}")
                return None