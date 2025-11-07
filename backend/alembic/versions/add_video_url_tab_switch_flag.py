"""Add video_url and tab_switch flag type

Revision ID: add_video_url_tab_switch
Revises: xxxxx_create_ai_interview
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_video_url_tab_switch'
down_revision: Union[str, None] = 'xxxxx_create_ai_interview'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add video_url column to ai_interview_sessions
    op.add_column('ai_interview_sessions', sa.Column('video_url', sa.Text(), nullable=True))
    
    # Note: The flag_type is stored as String/VARCHAR, not a PostgreSQL enum type
    # So we don't need to alter the enum - the application will handle the new 'tab_switch' value
    # If you're using a PostgreSQL enum type, you would need to:
    # op.execute("ALTER TYPE flag_type_enum ADD VALUE IF NOT EXISTS 'tab_switch'")


def downgrade() -> None:
    # Remove video_url column
    op.drop_column('ai_interview_sessions', 'video_url')
    
    # Note: We can't easily remove enum values from PostgreSQL enums
    # The application should handle 'tab_switch' flag_type gracefully

