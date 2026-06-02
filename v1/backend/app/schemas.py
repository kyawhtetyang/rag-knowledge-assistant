from __future__ import annotations

from pydantic import BaseModel, Field


class IngestTextRequest(BaseModel):
    source: str = Field(..., description='Logical source name (filename/URL/etc.)')
    text: str = Field(..., description='Raw text to ingest')
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: int
    chunks: int


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


class Citation(BaseModel):
    source: str
    chunk_index: int
    score: float
    preview: str


class AskResponse(BaseModel):
    question: str
    answer: str
    top_k: int
    citations: list[Citation]



class IngestFileResponse(BaseModel):
    filename: str
    document_id: int
    chunks: int



class IngestJobResponse(BaseModel):
    job_id: int
    status: str


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    source: str
    filename: str
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None



class EvalRunRequest(BaseModel):
    eval_set: str = 'default'
    top_k: int | None = None


class EvalRunResponse(BaseModel):
    run_id: int
    status: str


class EvalRunSummaryResponse(BaseModel):
    run_id: int
    status: str
    summary: dict
    created_at: str | None = None
    finished_at: str | None = None
