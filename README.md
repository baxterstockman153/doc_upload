# Doc Upload API

FastAPI + PostgreSQL backend that accepts PDF uploads, extracts patient data via Claude, and persists Orders.

---

## Setup

```bash
pip install -r requirements.txt
```

Set required environment variables:

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
export ANTHROPIC_API_KEY="sk-ant-..."
```

Run migrations (tables are also auto-created on startup via `create_all`):

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload
```

---

## Deployment (Render)

1. Create a new **Web Service** pointing to this repository.
2. Set environment variables in the Render dashboard:
   - `DATABASE_URL` — Render injects this automatically when a PostgreSQL database is attached.
   - `ANTHROPIC_API_KEY` — your Anthropic API key.
3. Set the **Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

Tables are created automatically on startup via SQLAlchemy `create_all`.

---

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/orders` | Create an order manually |
| GET | `/orders` | List all orders |
| GET | `/orders/{order_id}` | Get a single order |
| PUT | `/orders/{order_id}` | Update an order |
| DELETE | `/orders/{order_id}` | Delete an order |
| POST | `/orders/upload` | Upload a PDF, extract patient data, create order |
| GET | `/health` | Health check |

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

---

## Architecture & Design Decisions

### Layer responsibilities

| Layer | Responsibility |
|-------|---------------|
| `app/api/` | Route definitions, HTTP request/response, error translation |
| `app/services/` | Business logic, Claude API calls, DB operations |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic validation models |
| `app/core/` | Config, database engine, custom exceptions |
| `app/middleware/` | Cross-cutting concerns (activity logging) |

### Why extraction is synchronous

Extraction is currently handled synchronously in the request cycle for simplicity. The service interface (`extract_patient_data(raw_text)`) is deliberately isolated from the route layer so it can be moved to an async worker (Celery, ARQ) with minimal refactoring — the route would enqueue a task instead of calling the service directly, and the service code itself would be unchanged.

### Error handling

`ExtractionError` is raised in service layers and converted to HTTP 422 at route boundaries. Service layers never import from `fastapi`, keeping them portable and testable.

---

## Future Improvements

- **Async extraction queue** — move `extraction_service` calls into Celery/ARQ tasks; return a job ID and poll endpoint
- **Batch uploads** — accept multiple PDFs in a single request
- **JWT authentication** — protect all endpoints with Bearer token auth via FastAPI middleware
- **Rate limiting** — per-IP and per-API-key limits using `slowapi` or a Redis-backed solution
- **Claude retry logic** — exponential backoff around `client.messages.create` for transient API errors
- **Alembic migrations** — replace `create_all` with proper migration history for schema evolution
