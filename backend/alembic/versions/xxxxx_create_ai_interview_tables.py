"""Create AI Interview tables and extensions

Revision ID: xxxxx_create_ai_interview
Revises: 32276292d24b
Create Date: 2025-01-XX XX:XX:XX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'xxxxx_create_ai_interview'
down_revision: Union[str, None] = '32276292d24b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: PostgreSQL extensions must be created manually before running this migration
    # Run these SQL commands in your database first:
    # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    # CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Optional, for full-text search
    # CREATE EXTENSION IF NOT EXISTS "vector";   -- Optional, for vector similarity (install pgvector first)
    
    # Create ai_interview_sessions table
    op.create_table(
        'ai_interview_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='created'),
        sa.Column('total_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('recommendation', sa.String(), nullable=True),
        sa.Column('transcript_url', sa.Text(), nullable=True),
        sa.Column('report_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('policy_version', sa.String(50), nullable=False, server_default='1.0'),
        sa.Column('rubric_version', sa.String(50), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_application', 'ai_interview_sessions', ['application_id'])
    op.create_index('idx_session_job', 'ai_interview_sessions', ['job_id'])
    op.create_index('idx_session_status', 'ai_interview_sessions', ['status'])
    
    # Create ai_proctor_flags table
    op.create_table(
        'ai_proctor_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('flag_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('t_start', sa.Numeric(10, 3), nullable=False),
        sa.Column('t_end', sa.Numeric(10, 3), nullable=False),
        sa.Column('clip_url', sa.Text(), nullable=True),
        sa.Column('flag_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['ai_interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_flag_session_time', 'ai_proctor_flags', ['session_id', 't_start'])
    op.create_index('idx_flag_type', 'ai_proctor_flags', ['flag_type'])
    op.create_index('idx_flag_severity', 'ai_proctor_flags', ['severity'])
    
    # Create kb_docs table
    # Note: For pgvector, we'll use Text column initially, then migrate to vector type
    # The vector type requires the extension which we created above
    op.create_table(
        'kb_docs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('topic', sa.String(200), nullable=True),
        sa.Column('bucket', sa.String(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0'),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),  # Will be converted to vector in next migration
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_kb_role_level', 'kb_docs', ['role', 'level'])
    op.create_index('idx_kb_bucket', 'kb_docs', ['bucket'])
    op.create_index('idx_kb_topic', 'kb_docs', ['topic'])
    
    # Create GIN index for full-text search on kb_docs.text (requires pg_trgm)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kb_text_gin 
        ON kb_docs 
        USING gin(to_tsvector('english', text))
    """)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_kb_text_gin', 'kb_docs')
    op.drop_index('idx_kb_topic', 'kb_docs')
    op.drop_index('idx_kb_bucket', 'kb_docs')
    op.drop_index('idx_kb_role_level', 'kb_docs')
    op.drop_index('idx_flag_severity', 'ai_proctor_flags')
    op.drop_index('idx_flag_type', 'ai_proctor_flags')
    op.drop_index('idx_flag_session_time', 'ai_proctor_flags')
    op.drop_index('idx_session_status', 'ai_interview_sessions')
    op.drop_index('idx_session_job', 'ai_interview_sessions')
    op.drop_index('idx_session_application', 'ai_interview_sessions')
    
    # Drop tables
    op.drop_table('kb_docs')
    op.drop_table('ai_proctor_flags')
    op.drop_table('ai_interview_sessions')
    
    # Note: We don't drop extensions as they might be used by other tables

