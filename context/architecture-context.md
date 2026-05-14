# Architecture Context

## Stack

| Layer | Technology | Role |
|---|---|---|
| API Framework | FastAPI | HTTP endpoints and service entrypoint |
| Realtime | WebSocket | Streaming chat communication with clients |
| RAG | Custom Python services | Retrieval, context building, and answer generation |
| Vector Search | Qdrant | Semantic search over embedded document chunks |
| Database | PostgreSQL | Relational persistence for AI service data |
| Queue | Redis Streams | Background ingestion and processing jobs |
| Object Storage | S3-compatible storage | Source document storage and retrieval |
| AI Providers | OpenRouter / Ollama | LLM and embedding provider integrations |
| Backend Integration | Laravel/backend webhooks | Syncing status, conversation updates, and processing events |
| Runtime | Python | Application, workers, and service logic |


## System Boundaries

- `api` / `routes` — FastAPI request handlers, validation, and response wiring.
- `websocket` / `ws` — WebSocket connection lifecycle, chat events, and streaming responses.
- `services` — Application orchestration and business logic.
- `rag` — Retrieval, context construction, embeddings, chunking, and generation support.
- `workers` — Background jobs, Redis Streams processing, retries, and failure handling.
- `repositories` — PostgreSQL access and persistence logic.
- `providers` — OpenRouter, Ollama, and other AI provider adapters.
- `clients` / `integrations` — External service clients such as Qdrant, Redis, S3, and backend webhooks.
- `schemas` / `models` — Pydantic schemas, domain models, and database models.
- `tests` — Automated verification for API, WebSocket, RAG, workers, and integrations.



## Runtime Responsibilities

- FastAPI exposes service endpoints.
- WebSocket chat handles real-time user message flow.
- RAG retrieves relevant knowledge-base context for answers.
- Workers ingest documents asynchronously.
- Providers generate embeddings and AI responses.
- Integrations sync status and results back to the backend application.

## Data Responsibilities

- PostgreSQL stores AI-service records and processing state.
- Qdrant stores vectors for retrieval.
- Redis Streams carries background job messages.
- S3-compatible storage stores source documents.
- Laravel/backend owns user-facing business data.

## Contracts

- API request and response shapes should remain stable unless explicitly changed.
- WebSocket event names and payloads should remain stable unless explicitly changed.
- Worker job payloads should remain stable unless explicitly changed.
- Backend webhook payloads should remain stable unless explicitly changed.
- Provider interfaces should remain stable unless the task targets provider behavior.

## Invariants

1. FastAPI route handlers should stay thin and should not contain heavy AI or ingestion logic.
2. Long-running work belongs in workers or dedicated async processing flows.
3. WebSocket contracts must remain stable unless a task explicitly changes them.
4. RAG retrieval, ingestion, storage, and provider logic should remain separated.
5. PostgreSQL, Qdrant, Redis, and S3 each have separate storage responsibilities.
6. Provider adapters should hide OpenRouter/Ollama-specific details from application logic.
7. Backend/Laravel integration contracts must remain backward compatible unless explicitly changed.
8. Changes should preserve existing behavior unless the feature spec requires otherwise.


## Dependency Direction

Prefer this direction:

```text
api/routes -> application -> domain/services -> db/vector/providers/clients
```

Avoid reverse dependencies such as provider code importing route handlers or domain logic depending on FastAPI request objects.
