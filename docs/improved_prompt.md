# Improved Implementation Prompt

---

## PASTE-READY PROMPT (start copying below this line)

---

You are a senior Python backend engineer. Build a production-minded MVP backend for a take-home assignment.

---

## Working Style (mandatory)

- Generate files **one at a time**, in the exact order listed below.
- Do NOT output multiple files in one response.
- Before each file output:
  1. State the file path as a heading (e.g., `## app/core/config.py`)
  2. Write 1–3 sentences: purpose + what it exports + which tier it belongs to
  3. Output the full file in a single fenced code block
- After the code block, stop and wait. Do not start the next file until told.
- Do not leave TODOs unless explicitly noted.
- Do not add a frontend.
- Do not use Flask. FastAPI only.

---

## Goal

Build a publicly deployable FastAPI + PostgreSQL backend that:
- Exposes CRUD endpoints for an `Order` entity
- Accepts a single PDF upload, extracts patient data using Claude, and persists an `Order`
- Logs all API activity to the database via middleware
- Is structured so extraction can later be moved to an async worker queue with minimal refactoring

---

## Tech Stack (exact versions — do not substitute)

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
asyncpg==0.29.0
alembic==1.13.3
pydantic==2.9.2
pydantic-settings==2.5.2
anthropic==0.34.2
pypdf==4.3.1
python-multipart==0.0.12
```

These exact packages go in `requirements.txt`. Do not add, remove, or version-bump any of them.

---

## Database Rules (critical — do not deviate)

- Use `postgresql+asyncpg://` driver. **Never use SQLite**. Never write sync database code.
- `DATABASE_URL` from the environment will be in the form `postgresql://...` (Render injects this). You must replace the scheme: `DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)`.
- SQLAlchemy patterns:
  - Use `create_async_engine` from `sqlalchemy.ext.asyncio`
  - Use `async_sessionmaker` (SQLAlchemy 2.x), NOT `sessionmaker`
  - `Base` must inherit from `DeclarativeBase` (SQLAlchemy 2.x): `class Base(DeclarativeBase): pass`
  - Do NOT use `declarative_base()` (SQLAlchemy 1.x style)
  - All DB calls must be `await`-ed inside `async` functions
  - Session type: `AsyncSession` from `sqlalchemy.ext.asyncio`

---

## Pydantic Rules (critical — do not deviate)

- Use Pydantic v2 patterns only.
- For ORM-mode schemas: `model_config = ConfigDict(from_attributes=True)` — NOT `class Config: orm_mode = True`
- Validators: `@field_validator` — NOT `@validator`
- No `class Config:` blocks anywhere.

---

## Anthropic SDK Rules (critical — do not deviate)

- Import: `from anthropic import AsyncAnthropic`
- Instantiate: `client = AsyncAnthropic(api_key=settings.anthropic_api_key)`
- Call: `response = await client.messages.create(...)`  ← must be `await`-ed
- Extract text: `response.content[0].text`  ← NOT `response.text`
- Model name: `claude-3-5-haiku-20241022`
- Do not use `anthropic.Anthropic` (sync). Do not call `.complete()`. Do not access `.text` on the response object.

---

## PDF Extraction Rules

- Use `pypdf` only. Do not use PyMuPDF, pdfplumber, or any library not in `requirements.txt`.
- Pattern:
  ```python
  from pypdf import PdfReader
  import io

  reader = PdfReader(io.BytesIO(file_bytes))
  text = " ".join(page.extract_text() or "" for page in reader.pages)
  ```
- `page.extract_text()` may return `None` — always use `or ""`.

---

## Middleware Rules

- The activity logging middleware extends `BaseHTTPMiddleware`.
- `BaseHTTPMiddleware` **cannot use FastAPI dependency injection**. Do NOT attempt `Depends(get_db)` inside the middleware.
- Create the DB session directly: `async with AsyncSessionLocal() as db:`
- Do NOT read `response.body` inside middleware. Log request data only (method, path, status code, request_id).
- Assign `request_id` via `request.state.request_id = str(uuid.uuid4())` before calling `await call_next(request)`.

---

## Frozen Interface Contracts

Every service module must export exactly the following signatures. Do not rename, add optional parameters to, or restructure these functions.

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

Routes call these functions. Routes do not contain business logic or DB queries directly.

---

## Error Contract

- `ExtractionError` is a plain Python exception (not an `HTTPException`). Define it in `app/core/exceptions.py`.
- Service layers raise `ExtractionError` for Claude failures, malformed responses, and invalid extracted data.
- Route handlers catch `ExtractionError` and convert it to an `HTTPException(status_code=422)` at the boundary.
- Service layers never import from `fastapi`. Routes never contain extraction logic.

---

## Environment Variables

```
DATABASE_URL        # postgresql://... (Render provides this; code must rewrite scheme)
ANTHROPIC_API_KEY   # Anthropic API key
```

These are the only two required env vars. Load them via `pydantic-settings` in `app/core/config.py`.

---

## File Structure

```
requirements.txt
app/
  __init__.py
  main.py
  core/
    __init__.py
    config.py          # pydantic-settings Settings class
    database.py        # engine, AsyncSessionLocal, Base, get_db
    exceptions.py      # ExtractionError
  models/
    __init__.py
    order.py           # Order ORM model
    activity_log.py    # ActivityLog ORM model
  schemas/
    __init__.py
    patient.py         # PatientData (used internally by extraction_service)
    order.py           # OrderCreate, OrderUpdate, OrderResponse
  services/
    __init__.py
    document_service.py
    extraction_service.py
    order_service.py
  api/
    __init__.py
    orders.py          # CRUD routes
    uploads.py         # upload route
  middleware/
    __init__.py
    activity_logging.py
README.md
CONTEXT.md
```

---

## Dependency Tier Graph

Files within the same tier have no dependencies on each other and can be written in parallel. Files in a later tier depend on earlier tiers.

| Tier | Files |
|------|-------|
| 0 | `requirements.txt`, `app/core/exceptions.py`, `app/core/config.py`, `app/schemas/patient.py`, `app/schemas/order.py` |
| 1 | `app/core/database.py`, `app/models/order.py`, `app/models/activity_log.py` |
| 2 | `app/services/extraction_service.py`, `app/services/order_service.py` |
| 3 | `app/services/document_service.py`, `app/middleware/activity_logging.py` |
| 4 | `app/api/orders.py`, `app/api/uploads.py` |
| 5 | `app/main.py`, `README.md`, `CONTEXT.md` |

---

## Generation Order (follow exactly)

Generate files in this order, one at a time:

1. `requirements.txt`
2. `app/core/exceptions.py`
3. `app/core/config.py`
4. `app/schemas/patient.py`
5. `app/schemas/order.py`
6. `app/core/database.py`
7. `app/models/order.py`
8. `app/models/activity_log.py`
9. `app/services/extraction_service.py`
10. `app/services/order_service.py`
11. `app/services/document_service.py`
12. `app/middleware/activity_logging.py`
13. `app/api/orders.py`
14. `app/api/uploads.py`
15. `app/main.py`
16. `README.md`
17. `CONTEXT.md`

All `__init__.py` files are empty. Do not number them separately — emit them inline when creating the first file in each package directory.

---

## Domain Models

### Order (ORM: `app/models/order.py`)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | Integer | No | primary key, autoincrement |
| first_name | String(100) | No | |
| last_name | String(100) | No | |
| date_of_birth | Date | No | |
| source_file_name | String(255) | Yes | null if manually created |
| created_at | DateTime(timezone=True) | No | server_default=func.now() |
| updated_at | DateTime(timezone=True) | No | server_default=func.now(), onupdate=func.now() |

### ActivityLog (ORM: `app/models/activity_log.py`)

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

## Schemas

### `app/schemas/patient.py`

```python
from pydantic import BaseModel, field_validator
from datetime import date

class PatientData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
```

### `app/schemas/order.py`

```python
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional

class OrderCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    source_file_name: Optional[str] = None
    # validators: strip whitespace, reject empty, reject future dates, reject >120 years ago

class OrderUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    # same validators as OrderCreate, applied only to provided fields

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    source_file_name: Optional[str]
    created_at: datetime
    updated_at: datetime
```

---

## Validation Rules

### For `OrderCreate` / `OrderUpdate`

- `first_name`: required, strip whitespace, reject if empty after strip
- `last_name`: required, strip whitespace, reject if empty after strip
- `date_of_birth`: required, must be a valid date, must not be in the future, must not be more than 120 years in the past

### For upload extraction result

- Claude must return **only** a JSON object. No prose, no markdown fences.
- Parse with `json.loads()`. If it raises, raise `ExtractionError("Claude returned non-JSON response")`.
- Validate parsed dict against `PatientData`. If validation fails, raise `ExtractionError(f"Claude response failed schema validation: {e}")`.
- Do not persist if validation fails.

---

## API Endpoints

### Orders CRUD (`app/api/orders.py`)

| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | /orders | `OrderCreate` | `OrderResponse` 201 |
| GET | /orders | — | `list[OrderResponse]` 200 |
| GET | /orders/{order_id} | — | `OrderResponse` 200 |
| PUT | /orders/{order_id} | `OrderUpdate` | `OrderResponse` 200 |
| DELETE | /orders/{order_id} | — | 204 No Content |

Return 404 if order not found. Return 422 if validation fails (FastAPI handles Pydantic errors automatically).

### Upload (`app/api/uploads.py`)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | /orders/upload | `UploadFile` (form field: `file`) | `OrderResponse` 201 |

Upload behavior (exact sequence — implement in this order):
1. Validate content type: accept `application/pdf` only. Return 400 if not PDF.
2. Read file bytes: `file_bytes = await file.read()`
3. Call `document_service.extract_text_from_upload(file)` → `raw_text: str`
4. If `raw_text` is empty after stripping, return 422: `{"detail": "No text could be extracted from the document"}`
5. Call `extraction_service.extract_patient_data(raw_text)` → `PatientData`
6. Catch `ExtractionError` → return 422 with error detail
7. Build `OrderCreate` from `PatientData` fields + `source_file_name=file.filename`
8. Call `order_service.create_order(order_create, db)` → `Order`
9. Return `OrderResponse` with status 201

---

## Claude Prompt (use exactly)

When calling the Anthropic API in `extraction_service.py`, use this exact system/user prompt structure:

```python
response = await client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=256,
    system=(
        "You are a data extraction assistant. "
        "Extract patient information from the provided text. "
        "Return ONLY a JSON object with keys: first_name, last_name, date_of_birth (YYYY-MM-DD). "
        "Do not include any explanation, markdown, or text outside the JSON object."
    ),
    messages=[
        {"role": "user", "content": f"Extract patient information from this text:\n\n{raw_text}"}
    ],
)
raw_json = response.content[0].text
```

---

## Per-File Output Template

For every file you generate, use this structure:

```
## <file path>

**Tier:** <0–5>
**Purpose:** <one sentence>
**Exports:** <list of classes/functions this file exposes>
**Depends on:** <list of previously generated files this imports from>

**Do NOT:**
- <specific antipattern to avoid for this file>
- <another antipattern>

**Self-check before moving on:**
- [ ] All imports exist in previously generated files or stdlib/installed packages
- [ ] No sync DB calls (no `session.execute` without `await`)
- [ ] No `class Config:` blocks
- [ ] No `declarative_base()` calls
- [ ] Correct exception types (ExtractionError not HTTPException in services)

\```python
<full file contents>
\```
```

---

## `CONTEXT.md` Requirements (LLM-optimized)

Generate `CONTEXT.md` as the final file. It must contain exactly these sections, in this order:

```markdown
# CONTEXT.md — Backend System Overview

## Tech Stack
- Python 3.11
- FastAPI 0.115.0
- SQLAlchemy 2.0.35 (async, asyncpg driver)
- PostgreSQL (Render-hosted)
- Pydantic 2.9.2
- Anthropic SDK 0.34.2 (AsyncAnthropic, claude-3-5-haiku-20241022)
- pypdf 4.3.1

## File Map
<list every file with one-line description>

## Dependency Tier Graph
<reproduce the tier table>

## Frozen Interface Contracts
<reproduce the exact function signatures from the "Frozen Interface Contracts" section above>

## Data Models
<reproduce Order and ActivityLog column tables>

## Upload + Extraction Flow
<numbered steps, exactly matching the upload behavior sequence above>

## Validation Rules
<reproduce the validation rules>

## Error Contract
<describe ExtractionError, where it's raised, where it's caught>

## Environment Variables
<list DATABASE_URL and ANTHROPIC_API_KEY with descriptions>

## Known Constraints
- Single file upload only (no batch)
- Synchronous extraction (no queue)
- No authentication
- No rate limiting

## Extension Points
- Move extraction_service call into a Celery/ARQ task for async processing
- Add batch upload endpoint accepting multiple files
- Add JWT authentication via FastAPI middleware
- Add retry logic around Claude API calls with exponential backoff
```

Style: no prose, no marketing language, no storytelling. Structured lists and tables only.

---

## `README.md` Requirements

Include these sections:
1. **Setup** — `pip install -r requirements.txt`, set env vars, `alembic upgrade head`, `uvicorn app.main:app --reload`
2. **Deployment (Render)** — set `DATABASE_URL` and `ANTHROPIC_API_KEY` in Render environment; start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **API Overview** — table of all endpoints
4. **Architecture & Design Decisions** — layer responsibilities, why extraction is synchronous now but isolated for future queue migration
5. **Future Improvements** — batch uploads, async extraction queue, auth, rate limiting, retry logic

---

## Final Checklist (verify before CONTEXT.md)

Before generating `CONTEXT.md`, verify:
- [ ] `requirements.txt` uses exact pinned versions listed above
- [ ] `app/core/database.py` uses `create_async_engine`, `async_sessionmaker`, `DeclarativeBase`
- [ ] `app/core/database.py` rewrites `postgresql://` to `postgresql+asyncpg://`
- [ ] No file uses `declarative_base()`, `sessionmaker`, or `orm_mode = True`
- [ ] No file imports `HTTPException` in a service layer
- [ ] `extraction_service.py` awaits `client.messages.create(...)` and reads `response.content[0].text`
- [ ] `middleware/activity_logging.py` uses `AsyncSessionLocal()` directly, not `Depends(get_db)`
- [ ] `pypdf` is the only PDF library used; all `page.extract_text()` calls use `or ""`
- [ ] All `__init__.py` files are present (even if empty)

---

Now begin with file 1: `requirements.txt`

---

## END OF PASTE-READY PROMPT

---

# Summary of Changes

## Problems Fixed and How

### 1. SQLite removed entirely
**Before:** "local development may support SQLite if helpful"
**After:** Removed. PostgreSQL + asyncpg only. Models explicitly forbid sync drivers. The scheme-replacement one-liner (`DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)`) is pre-written so the model doesn't have to figure it out.

### 2. Frozen interface contracts added
**Before:** No function signatures specified; each layer invented its own API.
**After:** Exact Python signatures for all five service functions are frozen in the prompt. The model is told: "Do not rename, add optional parameters to, or restructure these." This prevents routes and services from drifting.

### 3. `ExtractionError` defined as a Tier 0 artifact
**Before:** No custom exception defined; models tended to raise `HTTPException` from service layers.
**After:** `ExtractionError` is a plain Python exception, defined in `app/core/exceptions.py` (Tier 0, no deps). Services raise it; routes catch it and convert to 422. Service layers are explicitly forbidden from importing `fastapi`.

### 4. Anthropic SDK call details pre-written
**Before:** No SDK usage specified; models hallucinated `.complete()`, `response.text`, sync `Anthropic()`.
**After:** Exact boilerplate provided: `AsyncAnthropic`, `await client.messages.create(...)`, `response.content[0].text`, model name `claude-3-5-haiku-20241022`. The model copies this directly.

### 5. SQLAlchemy 2.x async patterns mandated
**Before:** No patterns specified; models defaulted to 1.x `declarative_base()` + sync `sessionmaker`.
**After:** `create_async_engine`, `async_sessionmaker`, `class Base(DeclarativeBase): pass` are all required explicitly. Banned patterns listed: `declarative_base()`, `sessionmaker`, `orm_mode = True`.

### 6. Pydantic v2 patterns mandated
**Before:** No Pydantic version pinned; models used `class Config: orm_mode = True` and `@validator`.
**After:** `model_config = ConfigDict(from_attributes=True)` and `@field_validator` are required. `class Config:` blocks are banned explicitly in the per-file self-check.

### 7. Middleware session pattern specified
**Before:** No guidance; models attempted `Depends(get_db)` inside `BaseHTTPMiddleware` (crashes at runtime).
**After:** "Do NOT attempt `Depends(get_db)` inside the middleware" is stated explicitly. Direct `async with AsyncSessionLocal() as db:` pattern is mandated. Reading `response.body` is also explicitly banned.

### 8. PDF library mandated as `pypdf`
**Before:** No library specified; models chose PyMuPDF which requires system libs that fail on Render free tier.
**After:** `pypdf` only. Exact import + usage pattern pre-written. `page.extract_text() or ""` guard is shown inline.

### 9. Dependency tier graph added
**Before:** Files listed in order but no grouping; models didn't know which files were independent.
**After:** 6-tier dependency graph makes clear which files share no inter-dependencies and can be built by parallel agents. Each tier is a safe parallelization boundary.

### 10. Per-file output template with self-check
**Before:** Loose instruction: "state file path, purpose, dependencies."
**After:** Structured template with: Tier, Purpose, Exports, Depends On, explicit "Do NOT" list, and a 5-point self-check checklist the model runs before moving to the next file.

### 11. CONTEXT.md given exact section structure
**Before:** General requirements ("include architecture, data contracts, etc.").
**After:** Exact section headings, order, and content directives. Content points back to frozen sections of the prompt (interface contracts, validation rules, error contract) so CONTEXT.md stays in sync with the implementation.

### 12. File structure split into smaller modules
**Before:** `app/models.py`, `app/schemas.py`, `app/database.py`, `app/utils/settings.py`
**After:** `app/models/order.py` + `app/models/activity_log.py`, `app/schemas/patient.py` + `app/schemas/order.py`, `app/core/database.py`, `app/core/config.py`. Smaller files reduce context required per file and make parallel generation safer.

### 13. Upload endpoint behavior made sequential and numbered
**Before:** Described as a list of things to do; model could reorder or skip steps.
**After:** 9 numbered steps with exact function calls, variable names, error codes, and conditions. No ambiguity in order of operations.

### 14. Claude prompt pre-written verbatim
**Before:** Described what Claude should return; model wrote its own prompt (varied across runs).
**After:** System prompt and user message are written out exactly and told to be copied as-is. This eliminates prompt variance between runs.

### 15. Final checklist added
**Before:** No verification step.
**After:** 10-point boolean checklist the model runs before generating `CONTEXT.md`. Catches the most common failure modes (wrong ORM pattern, wrong SDK call, missing `__init__.py`) before the codebase is declared done.
