from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user
from app.models import User

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    email: str
    fullname: str | None = None
    is_active: bool


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
