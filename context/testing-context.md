# Testing Context

This file defines how tests should be written. It does not grant permission to run tests or execute commands.

## Framework

Use `pytest`.

Do not introduce a new testing framework or test dependency unless explicitly requested.

## Scope

Write tests only for the requested feature spec.

Prefer focused tests that clearly cover the requested behavior.

Do not add broad, unrelated, or opportunistic coverage.

Do not convert a unit-test task into an integration-test task.

## Style

- Keep tests small and readable.
- Use descriptive test names.
- Prefer one clear test per behavior.
- Use `pytest.mark.parametrize` when it reduces repetition.
- Avoid over-testing the same behavior with many similar cases.
- Do not depend on test execution order.

## Unit Tests

Unit tests must be isolated.

They must not require PostgreSQL, Qdrant, Redis, S3, AI providers, a running FastAPI server, or running workers.

Use simple fakes, monkeypatching, or fixtures only when needed.

## Integration Tests

Only write integration tests when explicitly requested.

Integration tests may cover service boundaries such as FastAPI, WebSocket, PostgreSQL, Qdrant, Redis Streams, S3-compatible storage, AI provider adapters, or background workers.

## File Placement

Use the existing test structure.

If no convention exists, prefer:

```text
tests/unit/
tests/integration/
````

Place tests near the responsibility being tested, such as:

```text
tests/unit/services/
tests/unit/domain/
tests/unit/api/
tests/unit/workers/
```

## Test Data

Keep test data minimal.

Use inline fixtures or small local fixtures when possible.

Do not use secrets, real credentials, or real user data.

Avoid large generated files unless the feature spec explicitly requires file-based testing.

## Verification

Do not mark work as tested, verified, or passing unless execution was explicitly allowed and actually performed.

If tests were added but not run, say so in the final response.