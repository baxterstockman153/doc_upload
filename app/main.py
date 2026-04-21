import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s: %(message)s")
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.middleware.activity_logging import ActivityLoggingMiddleware
from app.api import orders, uploads, activity_logs

# Import models so Base metadata is populated before create_all
import app.models.order  # noqa: F401
import app.models.activity_log  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Doc Upload API",
    description="FastAPI backend for structured data extraction from uploaded documents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(ActivityLoggingMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

app.include_router(orders.router)
app.include_router(uploads.router)
app.include_router(activity_logs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
