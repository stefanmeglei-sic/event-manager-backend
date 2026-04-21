# Event Manager Backend

FastAPI backend foundation for the university event management system.

## Setup

1. Create and activate a virtual environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template and adjust values:

```bash
cp .env.example .env
```

4. Run the server:

```bash
uvicorn main:app --reload
```

Server URL: http://127.0.0.1:8000

## API Docs

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Current Scope (Checkpoint 1)

- App structure and router skeletons
- Config and async DB session dependency
- Auth dependency stubs and role guard
- Placeholder endpoints for auth, users, events, lookups, registrations

Database migrations and full CRUD implementation are handled in later checkpoints.