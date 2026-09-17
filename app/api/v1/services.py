from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_salon
from app.core.database import get_db
from app.models.salon import Salon
from app.models.service import Service

router = APIRouter()

@router.get("/")
async def list_services(
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.salon_id == salon.id)
    )
    return result.scalars().all()