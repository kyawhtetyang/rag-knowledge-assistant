from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = 'documents'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column('metadata', JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chunks: Mapped[list['Chunk']] = relationship(back_populates='document', cascade='all, delete-orphan')

    __table_args__ = (UniqueConstraint('source', 'checksum', name='uq_documents_source_checksum'),)


class Chunk(Base):
    __tablename__ = 'chunks'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column('metadata', JSON, nullable=False, default=dict)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    document: Mapped['Document'] = relationship(back_populates='chunks')

    __table_args__ = (UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_doc_chunk_index'),)


class IngestionJob(Base):
    __tablename__ = 'ingestion_jobs'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    meta: Mapped[dict] = mapped_column('metadata', JSON, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvalSet(Base):
    __tablename__ = 'eval_sets'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvalItem(Base):
    __tablename__ = 'eval_items'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    eval_set_id: Mapped[int] = mapped_column(ForeignKey('eval_sets.id', ondelete='CASCADE'), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_contains: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvalRun(Base):
    __tablename__ = 'eval_runs'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    eval_set_id: Mapped[int] = mapped_column(ForeignKey('eval_sets.id', ondelete='CASCADE'), nullable=False)

    retrieval_mode: Mapped[str] = mapped_column(String, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_weight: Mapped[float] = mapped_column(sa.Float, nullable=False)
    fts_weight: Mapped[float] = mapped_column(sa.Float, nullable=False)

    embeddings_provider: Mapped[str] = mapped_column(String, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String, nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvalResult(Base):
    __tablename__ = 'eval_results'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    eval_run_id: Mapped[int] = mapped_column(ForeignKey('eval_runs.id', ondelete='CASCADE'), nullable=False)
    eval_item_id: Mapped[int] = mapped_column(ForeignKey('eval_items.id', ondelete='CASCADE'), nullable=False)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    hit: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    missing: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

