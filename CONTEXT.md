# CONTEXT.md — Backend System Overview

## Tech Stack
- Python 3.11
- FastAPI 0.115.0
- SQLAlchemy 2.0.35 (async, asyncpg driver)
- PostgreSQL (Render-hosted)
- Pydantic 2.9.2
- Anthropic SDK 0.34.2 (AsyncAnthropic, claude-3-5-haiku-20241022)
- pypdf 4.3.1

---

## File Map

| File | Description |
|------|-------------|
| `requirements.txt` | Pinned dependencies |
| `app/main.py` | FastAPI app, lifespan (create_all), middleware and router registration |
| `app/core/config.py` | pydantic-settings Settings class; loads DATABASE_URL, ANTHROPIC_API_KEY |
| `app/core/database.py` | Async engine, AsyncSessionLocal, Base (DeclarativeBase), get_db dependency |
| `app/core/exceptions.py` | ExtractionError — plain Python exception for Claude failures |
| `app/models/order.py` | Order ORM model |
| `app/models/activity_log.py` | ActivityLog ORM model |
| `app/schemas/patient.py` | PatientData — internal schema for Claude extraction output |
| `app/schemas/order.py` | OrderCreate, OrderUpdate, OrderResponse |
| `app/services/document_service.py` | Reads UploadFile bytes and extracts text via pypdf |
| `app/services/extraction_service.py` | Calls Claude API, parses JSON, returns PatientData |
| `app/services/order_service.py` | CRUD operations against the orders table |
| `app/api/orders.py` | CRUD routes for /orders |
| `app/api/uploads.py` | POST /orders/upload route |
| `app/middleware/activity_logging.py` | BaseHTTPMiddleware that logs every request to activity_logs |

---

## Dependency Tier Graph

| Tier | Files |
|------|-------|
| 0 | `requirements.txt`, `app/core/exceptions.py`, `app/core/config.py`, `app/schemas/patient.py`, `app/schemas/order.py` |
| 1 | `app/core/database.py`, `app/models/order.py`, `app/models/activity_log.py` |
| 2 | `app/services/extraction_service.py`, `app/services/order_service.py` |
| 3 | `app/services/document_service.py`, `app/middleware/activity_logging.py` |
| 4 | `app/api/orders.py`, `app/api/uploads.py` |
| 5 | `app/main.py`, `README.md`, `CONTEXT.md` |

---

## Frozen Interface Contracts

```python
# app/services/document_service.py
async def extract_text_from_upload(file: UploadFile) -> str: ...

# app/services/extraction_service.py
async def extract_patient_data(raw_text: str) -> PatientData: ...
#   raises ExtractionError if Claude call fails or response is malformed

# app/services/order_service.py
async def create_order(data: OrderCreate, db: AsyncSession) -> Order: ...
async def get_order(order_id: int, db: AsyncSession) -> Order: ...
async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Order]: ...
async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession) -> Order: ...
async def delete_order(order_id: int, db: AsyncSession) -> None: ...
```

---

## Data Models

### Order

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | Integer | No | primary key, autoincrement |
| first_name | String(100) | No | |
| last_name | String(100) | No | |
| date_of_birth | Date | No | |
| source_file_name | String(255) | Yes | null if manually created |
| created_at | DateTime(timezone=True) | No | server_default=func.now() |
| updated_at | DateTime(timezone=True) | No | server_default=func.now(), onupdate=func.now() |

### ActivityLog

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | Integer | No | primary key, autoincrement |
| method | String(10) | No | |
| path | String(500) | No | |
| status_code | Integer | No | |
| request_id | String(36) | No | UUID string |
| error_message | Text | Yes | |
| created_at | DateTime(timezone=True) | No | server_default=func.now() |

---

## Upload + Extraction Flow

1. Validate content type: accept `application/pdf` only — return 400 if not PDF
2. Read file bytes via `await file.read()`
3. Call `document_service.extract_text_from_upload(file)` → `raw_text: str`
4. If `raw_text.strip()` is empty, return 422: `{"detail": "No text could be extracted from the document"}`
5. Call `extraction_service.extract_patient_data(raw_text)` → `PatientData`
6. Catch `ExtractionError` → return 422 with error detail
7. Build `OrderCreate` from `PatientData` fields + `source_file_name=file.filename`
8. Call `order_service.create_order(order_create, db)` → `Order`
9. Return `OrderResponse` with status 201

---

## Validation Rules

### OrderCreate / OrderUpdate
- `first_name`: required, strip whitespace, reject if empty after strip
- `last_name`: required, strip whitespace, reject if empty after strip
- `date_of_birth`: required, must not be in the future, must not be more than 120 years in the past

### Extraction result
- Claude must return only a JSON object (no prose, no markdown fences)
- Parse with `json.loads()` — if it raises, raise `ExtractionError("Claude returned non-JSON response")`
- Validate parsed dict against `PatientData` — if validation fails, raise `ExtractionError(f"Claude response failed schema validation: {e}")`
- Do not persist if validation fails

---

## Error Contract

- `ExtractionError` is defined in `app/core/exceptions.py` as a plain Python exception
- Raised by `extraction_service.extract_patient_data` when:
  - Claude API call fails (any exception from the SDK)
  - Claude returns non-JSON text
  - Parsed JSON fails `PatientData` schema validation
- Caught by `app/api/uploads.py` and converted to `HTTPException(status_code=422)`
- Service layers never import from `fastapi`
- Routes never contain extraction logic

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string in the form `postgresql://...` (Render injects this); code rewrites scheme to `postgresql+asyncpg://` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude API access |

---

## Known Constraints
- Single file upload only (no batch)
- Synchronous extraction (no queue)
- No authentication
- No rate limiting

---

## Extension Points
- Move extraction_service call into a Celery/ARQ task for async processing
- Add batch upload endpoint accepting multiple files
- Add JWT authentication via FastAPI middleware
- Add retry logic around Claude API calls with exponential backoff
