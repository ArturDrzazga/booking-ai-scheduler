from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import admin, auth, bookings, chat, payments, services, staff, users
from app.core.config import settings
from app.core.database import get_db
from app.tasks import test_task

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Async REST API for beauty salon booking with AI assistant",
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

security = HTTPBearer()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(staff.router, prefix="/api/v1/staff", tags=["staff"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["booking"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/db-test")
async def test_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"status": "ok", "message": "Database connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/test-celery")
async def test_celery():
    task = test_task.delay()
    return {"task_id": task.id, "status": "sent"}

@app.get("/chat", response_class=HTMLResponse, response_model=None)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat/index.html", {"request": request})