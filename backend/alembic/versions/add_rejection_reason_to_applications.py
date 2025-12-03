"""Add rejection_reason column to applications

Revision ID: add_rejection_reason_to_applications
Revises: add_video_url_tab_switch
Create Date: 2025-11-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_rejection_reason_to_applications"
down_revision: Union[str, None] = "add_video_url_tab_switch"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE applications ADD COLUMN IF NOT EXISTS rejection_reason TEXT"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE applications DROP COLUMN IF EXISTS rejection_reason")

