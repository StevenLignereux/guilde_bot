from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.config.database import Base

class TaskList(Base):
    __tablename__ = "task_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_discord_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    
    tasks = relationship("Task", back_populates="task_list", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    task_list_id = Column(Integer, ForeignKey("task_lists.id"))
    
    task_list = relationship("TaskList", back_populates="tasks") 