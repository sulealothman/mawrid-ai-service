# Code Standards

## General

- Keep modules and functions small, focused, and easy to test.
- Fix root causes instead of adding workarounds.
- Do not mix unrelated concerns in one module, route, service, or worker.
- Respect the system boundaries defined in `context/architecture-context.md`.

## Runtime Commands

Do not run the project or execute runtime commands unless explicitly instructed.

This includes Docker Compose, Python, pytest, alembic, uvicorn, workers, database commands, Redis, Qdrant, or S3-related commands.

Writing code, writing tests, or updating documentation does not imply permission to run commands.

## Python

- Use Python type hints when adding or modifying functions.
- Preserve async boundaries. Do not call async APIs from sync functions without a clear bridge.
- Avoid blocking I/O inside async routes, WebSocket handlers, and worker loops.
- Prefer `from __future__ import annotations` in files already using it.
- Do not catch broad exceptions unless the existing flow requires resilience.
- Do not swallow exceptions silently in new code. Preserve useful error details and add safe logging when appropriate.

## FastAPI

- Keep route handlers small.
- Validate inbound payloads with Pydantic schemas.
- Put authentication and provider wiring in `app/api/deps/` where possible.
- Keep business logic in `app/application/`, `app/domain/`, or `app/services/`.
- Do not introduce new route prefixes without updating the relevant context docs.

## WebSocket

- Preserve current event names unless explicitly changed by the task.
- Inbound events: `message.send`, `generation.cancel`.
- Outbound events: `ready`, `ack`, `status`, `delta`, `done`, `cancelled`, `error`.
- Include `request_id` when an event relates to a specific generation.
- Cancel active tasks on disconnect and close provider clients safely.
- Avoid concurrent writes to the same WebSocket unless protected by synchronization.

## RAG

- Always scope retrieval by `kb_id`.
- Do not mix chunks from different knowledge bases.
- Preserve source metadata in responses.
- Do not increase `MAX_CONTEXT_CHARS`, `top_k`, chunk size, or embedding batch size without considering context, latency, and cost.
- Chunking or vector payload changes must consider backward compatibility, reindexing, and migration implications.

## Database

- Use the existing `AsyncSessionLocal` and SQLAlchemy async patterns.
- Schema changes require Alembic migrations under `app/alembic/versions/`.
- Keep PostgreSQL as the source of truth for chunk text.
- Do not rely on Qdrant as the only copy of source text.

## Worker

- Preserve Redis Stream ack/retry/DLQ behavior.
- Do not ack failed jobs before failure handling is complete.
- Keep webhook status reporting compatible with the Laravel backend.
- Clean up temporary files after processing.
- Validate external job payloads before processing.

## Testing

Follow `context/testing-context.md`.

Do not run tests unless explicitly instructed.

## File Organization

Use the existing project structure as the source of truth.

Place new code next to the closest existing responsibility area. Do not introduce new top-level directories, route groups, provider layers, or worker patterns unless explicitly requested or documented in the context files.

Name files after the responsibility they contain, not the technology alone.