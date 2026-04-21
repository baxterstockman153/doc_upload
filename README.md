# Doc Upload

Doc Upload is a full-stack application that streamlines patient data entry from paper documents. Upload a PDF containing patient information, and Claude AI (Haiku) extracts structured data — patient name and date of birth — which is persisted as an Order in PostgreSQL and immediately viewable through a Next.js frontend. The flow is: browser → Next.js frontend → FastAPI backend → Claude document API → PostgreSQL, with all orders accessible via a live dashboard.

---

## Live Demo

| | URL |
|---|---|
| Frontend | https://doc-upload-ruby.vercel.app |
| Backend API | https://doc-upload-s5da.onrender.com |
| API Docs (Swagger) | https://doc-upload-s5da.onrender.com/docs |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / FastAPI / SQLAlchemy (async) / PostgreSQL / Anthropic SDK (Claude Haiku) |
| Frontend | Next.js 14 / React 18 / TypeScript / Tailwind CSS |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Design Choices

**Layered architecture** — routes handle HTTP only; services contain business logic; models and schemas are separate. No FastAPI imports in the service layer, keeping it portable and independently testable.

**Claude for PDF extraction** — PDFs are sent directly to Claude's document API (base64 encoded); no pre-processing step needed. Claude Haiku was chosen for cost efficiency on simple extraction tasks.

**Synchronous extraction** — extraction runs in-request-cycle for simplicity. The service interface is isolated from the route layer, so it can be moved to a task queue (Celery/ARQ) with minimal refactoring — the route would enqueue a task; the service code itself would be unchanged.

**Custom `ExtractionError`** — bridges the service layer to HTTP 422 without coupling services to FastAPI.

**Activity logging middleware** — every request is logged to PostgreSQL via `BaseHTTPMiddleware`; logging failures never bubble up to break the response.

**Async database** — SQLAlchemy async engine with asyncpg for non-blocking DB I/O.

**Pydantic validation** — input sanitization (strip whitespace, reject empty names, reject future DOBs) runs at the schema layer on ingestion, not at the route level.

---

## Running Locally

**Prerequisites:** Python 3.11+, Node.js 18+, a PostgreSQL database, an Anthropic API key

### Backend

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/docupload"
export ANTHROPIC_API_KEY="sk-ant-..."
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Frontend

```bash
cd frontend
npm install
# .env.local already contains NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

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

## Architecture

| Layer | Responsibility |
|-------|---------------|
| `app/api/` | Route definitions, HTTP request/response, error translation |
| `app/services/` | Business logic, Claude API calls, DB operations |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic validation models |
| `app/core/` | Config, database engine, custom exceptions |
| `app/middleware/` | Cross-cutting concerns (activity logging) |

---

## Future Improvements

- **Async extraction queue** — move `extraction_service` calls into Celery/ARQ tasks; return a job ID and poll endpoint
- **Batch uploads** — accept multiple PDFs in a single request
- **JWT authentication** — protect all endpoints with Bearer token auth via FastAPI middleware
- **Rate limiting** — per-IP and per-API-key limits using `slowapi` or a Redis-backed solution
- **Claude retry logic** — exponential backoff around `client.messages.create` for transient API errors
- **Alembic migrations** — replace `create_all` with proper migration history for schema evolution
- **PDF text pre-extraction** — use a library like PyMuPDF or pdfplumber to extract raw text from the PDF before sending to Claude, then pass only the text in the prompt instead of the full binary document. This reduces token usage on large PDFs (images, embedded fonts, etc. inflate cost when sent via the document API) and makes the LLM call cheaper, though it trades off Claude's native layout/table understanding.
