from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from api.app.db import get_db
from api.app.schemas.models import PortBase, PortCongestion
from api.app.core.security import get_current_user

router = APIRouter(prefix="/ports", tags=["Ports"], dependencies=[Depends(get_current_user)])

@router.get("/", response_model=List[PortBase])
async def list_ports(skip: int = 0, limit: int = Query(50, le=100), db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM gold.dim_port ORDER BY port_id OFFSET :skip LIMIT :limit"), {"skip": skip, "limit": limit})
    return [dict(r) for r in result.mappings().all()]

@router.get("/{port_id}", response_model=PortBase)
async def get_port(port_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM gold.dim_port WHERE port_id = :pid"), {"pid": port_id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Port not found")
    return dict(row)

@router.get("/{port_id}/congestion", response_model=List[PortCongestion])
async def get_port_congestion(port_id: str, limit: int = 24, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT port_id, hour, unique_vessels, avg_speed_knots, congestion_score, congestion_level FROM gold.agg_port_congestion WHERE port_id = :pid ORDER BY hour DESC LIMIT :limit"),
        {"pid": port_id, "limit": limit}
    )
    return [dict(r) for r in result.mappings().all()]
