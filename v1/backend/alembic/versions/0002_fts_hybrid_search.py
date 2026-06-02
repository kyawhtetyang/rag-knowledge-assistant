"""fts + hybrid retrieval

Revision ID: 0002_fts_hybrid_search
Revises: 0001_init
Create Date: 2026-05-31

"""

from alembic import op
import sqlalchemy as sa


revision = '0002_fts_hybrid_search'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Full-text search: generated tsvector column + GIN index.
    op.execute(
        """
        ALTER TABLE chunks
          ADD COLUMN IF NOT EXISTS content_tsv tsvector
          GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;
        """
    )
    op.execute('CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON chunks USING GIN (content_tsv);')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS idx_chunks_content_tsv;')
    op.execute('ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv;')
