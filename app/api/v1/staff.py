from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_salon
from app.core.database import get_db
from app.models import Salon, Staff

router = APIRouter()


class StaffCreate(BaseModel):
    name: str
    bio: str | None = None
    photo_url: str | None = None


class StaffUpdate(BaseModel):
    name: str | None = None
    bio: str | None = None
    photo_url: str | None = None


class StaffResponse(BaseModel):
    id: int
    name: str
    bio: str | None
    photo_url: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[StaffResponse])
async def list_staff(
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Staff).where(
            Staff.salon_id == salon.id
        )
    )
    return result.scalars().all()

@router.post("/", response_model=StaffResponse)
async def create_staff(
        data: StaffCreate,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    staff = Staff(
        salon_id=salon.id,
        name=data.name,
        bio=data.bio,
        photo_url=data.photo_url,
    )
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff

@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
        staff_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.salon_id == salon.id
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
        staff_id: int,
        data: StaffUpdate,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.salon_id == salon.id
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(staff, key, value)

    await db.commit()
    await db.refresh(staff)
    return staff

@router.delete("/{staff_id}")
async def delete_staff(
        staff_id: int,
        salon: Salon = Depends(get_current_salon),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.salon_id == salon.id
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    await db.delete(staff)
    await db.commit()
    return {"message": "Staff deleted"}