from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from api.app.db import get_db
from api.app.schemas.models import RouteIntelligence
from api.app.core.security import get_current_user

router = APIRouter(prefix="/routes", tags=["Routes"], dependencies=[Depends(get_current_user)])

@router.get("/", response_model=List[RouteIntelligence])
async def list_routes(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM gold.route_intelligence ORDER BY frequency DESC LIMIT :limit"), {"limit": limit})
    return [dict(r) for r in result.mappings().all()]
