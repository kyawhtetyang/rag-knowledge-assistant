"""eval runs

Revision ID: 0004_eval_runs
Revises: 0003_ingestion_jobs
Create Date: 2026-06-01

"""

from alembic import op
import sqlalchemy as sa


revision = '0004_eval_runs'
down_revision = '0003_ingestion_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'eval_sets',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'eval_items',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('eval_set_id', sa.BigInteger(), sa.ForeignKey('eval_sets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('expected_contains', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_eval_items_eval_set_id', 'eval_items', ['eval_set_id'])

    op.create_table(
        'eval_runs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('eval_set_id', sa.BigInteger(), sa.ForeignKey('eval_sets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('retrieval_mode', sa.String(), nullable=False),
        sa.Column('top_k', sa.Integer(), nullable=False),
        sa.Column('vector_weight', sa.Float(), nullable=False),
        sa.Column('fts_weight', sa.Float(), nullable=False),
        sa.Column('embeddings_provider', sa.String(), nullable=False),
        sa.Column('embedding_model', sa.String(), nullable=False),
        sa.Column('embedding_dim', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_eval_runs_eval_set_id', 'eval_runs', ['eval_set_id'])
    op.create_index('idx_eval_runs_status', 'eval_runs', ['status'])

    op.create_table(
        'eval_results',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('eval_run_id', sa.BigInteger(), sa.ForeignKey('eval_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('eval_item_id', sa.BigInteger(), sa.ForeignKey('eval_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('hit', sa.Boolean(), nullable=False),
        sa.Column('missing', sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_eval_results_run_id', 'eval_results', ['eval_run_id'])


def downgrade() -> None:
    op.drop_index('idx_eval_results_run_id', table_name='eval_results')
    op.drop_table('eval_results')

    op.drop_index('idx_eval_runs_status', table_name='eval_runs')
    op.drop_index('idx_eval_runs_eval_set_id', table_name='eval_runs')
    op.drop_table('eval_runs')

    op.drop_index('idx_eval_items_eval_set_id', table_name='eval_items')
    op.drop_table('eval_items')

    op.drop_table('eval_sets')
