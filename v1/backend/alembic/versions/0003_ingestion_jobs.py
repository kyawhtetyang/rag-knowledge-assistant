"""ingestion jobs

Revision ID: 0003_ingestion_jobs
Revises: 0002_fts_hybrid_search
Create Date: 2026-06-01

"""

from alembic import op
import sqlalchemy as sa


revision = '0003_ingestion_jobs'
down_revision = '0002_fts_hybrid_search'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_ingestion_jobs_status', 'ingestion_jobs', ['status'])
    op.create_index('idx_ingestion_jobs_created_at', 'ingestion_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_ingestion_jobs_created_at', table_name='ingestion_jobs')
    op.drop_index('idx_ingestion_jobs_status', table_name='ingestion_jobs')
    op.drop_table('ingestion_jobs')
