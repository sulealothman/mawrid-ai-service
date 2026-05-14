# Development Rules

## Operating Mode

Work only from the provided feature spec and context files.

Implement the requested feature spec, update `context/progress-tracker.md` after meaningful changes, and return a concise summary.

Do not expand scope, invent behavior, redesign architecture, or change contracts unless explicitly required by the feature spec.

## No Execution

Do not execute commands unless the user explicitly asks for the exact command.

This includes Docker Compose, Python, pytest, alembic, uvicorn, workers, scripts, database commands, Redis, Qdrant, S3, package installation, linting, formatting, type-checking, or verification commands.

Repository inspection and file editing only.

Writing code, tests, or docs does not imply permission to run anything.

## No Dependencies or Logs

Do not install, upgrade, remove, or replace dependencies unless explicitly requested.

Do not modify package manifests or lock files unless the feature spec explicitly requires it.

Do not read or rely on runtime logs unless the user explicitly provides logs or asks you to inspect them.

## Scope Control

Work on one feature unit at a time.

Prefer small, reviewable changes.

Split or document a blocker in `context/progress-tracker.md` if the requested change spans unrelated boundaries, such as API + workers, WebSocket + RAG, storage + schema, providers + business logic, or queue + API behavior.

## Missing Requirements

Do not invent missing requirements.

If a requirement is ambiguous or missing, record it as an open question in `context/progress-tracker.md`.

If implementation cannot continue safely, stop after documenting the blocker.

## Protected Code

Do not modify shared foundation code unless explicitly required.

Protected areas include generated files, core app/bootstrap config, database/session setup, shared clients, shared utilities, and existing API/WebSocket/worker/integration contracts.

Prefer feature-level modules over changing shared foundation code.

## Docs Sync

Update relevant context files when implementation changes architecture, contracts, storage decisions, RAG behavior, code conventions, feature scope, or progress.

Do not mark work as tested, verified, or passing unless the user explicitly allowed execution and it was actually performed.

If tests were added but not run, say so.

## Final Response

Keep the final response short.

Include only:

- What changed
- Files changed
- Tests added or updated, if any
- Verification status