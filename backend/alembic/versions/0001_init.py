"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-05-30

"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    op.create_table(
        'documents',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('checksum', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('source', 'checksum', name='uq_documents_source_checksum'),
    )

    op.create_table(
        'chunks',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('document_id', sa.BigInteger(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('embedding', Vector(384), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_doc_chunk_index'),
    )

    op.create_index('idx_chunks_document_id', 'chunks', ['document_id'])


def downgrade() -> None:
    op.drop_index('idx_chunks_document_id', table_name='chunks')
    op.drop_table('chunks')
    op.drop_table('documents')
