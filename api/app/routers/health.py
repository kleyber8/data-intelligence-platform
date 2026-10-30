from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
from api.app.db import get_db
from api.app.schemas.models import HealthStatus

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    return HealthStatus(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )
