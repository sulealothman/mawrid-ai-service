# Mawrid AI Service

## Overview

Mawrid AI Service is an existing Python microservice for document-based AI question answering.

It receives knowledge-base files from an external backend, extracts and chunks document text, embeds chunks into Qdrant, retrieves relevant context at chat time, and streams AI responses to clients over WebSocket.

This service is not a standalone frontend application. It is used by a backend application, likely Laravel.

## Goals

- Maintain the existing Python AI service without redesigning it.
- Keep FastAPI HTTP routes and WebSocket event contracts stable.
- Keep the RAG pipeline reliable, traceable, and easy to verify.
- Support safe document ingestion, retrieval, and answer generation.
- Keep background workers focused, idempotent, and recoverable.
- Maintain clean boundaries between API, WebSocket, RAG, storage, providers, and workers.
- Prefer small, testable changes over broad refactors.

## Core User Flow

1. A client application authenticates the user.
2. The user opens or creates a conversation.
3. The user selects or is assigned a knowledge base.
4. The user uploads documents or uses existing indexed content.
5. The user sends a chat message.
6. The AI service retrieves relevant knowledge-base context.
7. The AI response is streamed back over WebSocket.
8. Conversation state is finalized through backend integration.

## Scope

This project focuses only on the Python AI service layer.

### In scope

- FastAPI service endpoints.
- WebSocket chat and streaming responses.
- Knowledge-base grounded RAG.
- Document ingestion, extraction, chunking, embedding, and indexing.
- Background ingestion workers using Redis Streams.
- PostgreSQL persistence used by the AI service.
- Qdrant vector search.
- S3-compatible document storage.
- Backend/Laravel webhook integration.
- AI provider integration through OpenRouter and Ollama.
- Health/status checks.

### Out of scope

- Frontend UI implementation.
- Laravel application business logic.
- Billing or subscription systems.
- User-facing project/workspace management.
- Mobile applications.
- Admin dashboards.
- Replacing existing storage, queue, or AI provider architecture.
- Large architecture rewrites unless explicitly requested.

## Success Criteria

1. The service starts successfully and exposes a health/status endpoint.
2. Clients can connect to the WebSocket chat endpoint.
3. Authenticated chat requests can produce streamed AI responses.
4. Responses can use relevant context from indexed knowledge bases.
5. Documents can be ingested, chunked, embedded, and indexed.
6. Background ingestion jobs are processed reliably.
7. Backend synchronization and existing API, WebSocket, worker, RAG, and integration contracts remain stable unless explicitly changed.