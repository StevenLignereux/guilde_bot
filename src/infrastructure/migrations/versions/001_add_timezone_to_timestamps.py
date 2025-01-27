"""Migration pour ajouter le support des timezones aux colonnes de timestamp

Revision ID: 001_add_timezone_to_timestamps
Revises: 
Create Date: 2024-01-25 16:24:38.383612

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC

# revision identifiers, used by Alembic.
revision = '001_add_timezone_to_timestamps'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Mettre à jour la colonne created_at de task_lists
    op.alter_column('task_lists', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'',
                    existing_type=sa.DateTime(),
                    nullable=True)
    
    # Mettre à jour la colonne created_at de tasks
    op.alter_column('tasks', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'',
                    existing_type=sa.DateTime(),
                    nullable=True)

def downgrade() -> None:
    # Retirer le timezone de la colonne created_at de task_lists
    op.alter_column('task_lists', 'created_at',
                    type_=sa.DateTime(),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True)
    
    # Retirer le timezone de la colonne created_at de tasks
    op.alter_column('tasks', 'created_at',
                    type_=sa.DateTime(),
                    postgresql_using='created_at AT TIME ZONE \'UTC\'',
                    existing_type=sa.DateTime(timezone=True),
                    nullable=True) 