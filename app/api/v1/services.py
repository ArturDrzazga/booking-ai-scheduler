from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_salon
from app.core.database import get_db
from app.models.salon import Salon
from app.models.service import Service

router = APIRouter()

class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    duration_time: int
    price: float


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_time: int | None = None
    price: float | None = None


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    duration_time: int
    price: float
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ServiceResponse])
async def list_services(
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(Service.salon_id == salon.id)
    )
    return result.scalars().all()

@router.post("/", response_model=ServiceResponse)
async def create_service(
        data: ServiceCreate,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    service = Service(
        salon_id=salon.id,
        name=data.name,
        description=data.description,
        duration_time=data.duration_time,
        price=data.price,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
        service_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.salon_id == salon.id,
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
        service_id: int,
        data: ServiceUpdate,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.salon_id == salon.id,
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service

@router.delete("/{service_id}")
async def delete_service(
        service_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.salon_id == salon.id,
        )
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    await db.delete(service)
    await db.commit()
    return {"message": "Service deleted"}