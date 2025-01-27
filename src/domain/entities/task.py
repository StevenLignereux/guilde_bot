from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.config.database import Base

class TaskList(Base):
    """Représente une liste de tâches"""
    __tablename__ = "task_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_discord_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    tasks = relationship("Task", back_populates="task_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TaskList(id={self.id}, name='{self.name}', user_discord_id='{self.user_discord_id}')>"

class Task(Base):
    """Représente une tâche dans une liste"""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    task_list_id: Mapped[int] = mapped_column(Integer, ForeignKey("task_lists.id"), nullable=False)
    task_list = relationship("TaskList", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, description='{self.description}', completed={self.completed})>"

    def can_transition_to(self, new_status: str) -> bool:
        """Vérifie si la tâche peut passer au nouveau statut"""
        # Pour l'instant, on autorise toutes les transitions
        return True 