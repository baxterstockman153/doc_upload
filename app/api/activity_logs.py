from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.activity_log import ActivityLogResponse
from app.services import activity_log_service

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@router.get("", response_model=list[ActivityLogResponse])
async def list_activity_logs(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await activity_log_service.get_activity_logs(db, skip=skip, limit=limit)
