# Project Overview

## Pipeline

Text documents
-> Embedding model
-> Vector database (pgvector)
-> User question
-> Query embedding
-> Vector similarity search
-> Relevant chunks
-> LLM answer

## Components

- `backend/src/ingest.py`: loads files, chunks text, writes embeddings + metadata.
- `backend/src/retriever.py`: embeds query and runs vector similarity search.
- `backend/src/llm.py`: generates final answer using retrieved context.
- `backend/src/app.py`: HTTP API orchestration.
- `frontend/index.html`: minimal UI for ingestion and Q&A.

## Data Model

Single table `chunks` in Postgres:

- `doc_name`
- `chunk_index`
- `content`
- `metadata` (`jsonb`)
- `embedding` (`vector`)

Unique key: `(doc_name, chunk_index)`.
