import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.database import AsyncSessionLocal
from app.models.activity_log import ActivityLog


class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)

        error_message = None
        if response.status_code >= 400:
            error_message = f"HTTP {response.status_code}"

        try:
            async with AsyncSessionLocal() as db:
                log = ActivityLog(
                    method=request.method,
                    path=str(request.url.path),
                    status_code=response.status_code,
                    request_id=request.state.request_id,
                    error_message=error_message,
                )
                db.add(log)
                await db.commit()
        except Exception:
            pass  # Never let logging failures affect the response

        return response
