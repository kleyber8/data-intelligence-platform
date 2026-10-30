from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from api.app.db import get_db
from api.app.schemas.models import VesselProfile, Voyage
from api.app.core.security import get_current_user

router = APIRouter(prefix="/vessels", tags=["Vessels"], dependencies=[Depends(get_current_user)])

@router.get("/{vessel_id}", response_model=VesselProfile)
async def get_vessel(vessel_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM gold.vessel_intelligence WHERE mmsi = :mmsi"), {"mmsi": vessel_id})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return dict(row)

@router.get("/{vessel_id}/voyages", response_model=List[Voyage])
async def get_vessel_voyages(vessel_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM gold.fact_vessel_voyage WHERE mmsi = :mmsi ORDER BY start_ts DESC"), {"mmsi": vessel_id})
    return [dict(r) for r in result.mappings().all()]
