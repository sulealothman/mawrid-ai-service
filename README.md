# Mawrid AI Service (Alpha)

AI ingestion and processing service for the Mawrid knowledge platform.

## Overview

Mawrid AI Service is responsible for processing documents and generating vector embeddings used for semantic search.

It handles:

- Document ingestion
- Text extraction and chunking
- Embedding generation
- Vector storage
- Metadata persistence

The service consumes ingestion jobs from Redis streams, processes files stored in object storage, and stores embeddings in the vector database for retrieval.

## Infrastructure & Setup

Development environment, containers, and infrastructure configuration are managed in:

**mawrid-infra**