from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.activity_log import ActivityLog


async def get_activity_logs(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())
