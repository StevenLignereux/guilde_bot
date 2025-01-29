"""create task tables

Revision ID: 002_create_task_tables
Revises: 001_add_timezone_to_timestamps
Create Date: 2024-01-29 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC

# revision identifiers, used by Alembic.
revision = '002_create_task_tables'
down_revision = '001_add_timezone_to_timestamps'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Créer la table task_lists
    op.create_table(
        'task_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('user_discord_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Créer la table tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('task_list_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['task_list_id'], ['task_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('task_lists') 