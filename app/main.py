from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.tasks import test_task

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Async REST API for beauty salon booking with AI assistant",
)


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
