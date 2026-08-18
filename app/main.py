from fastapi import FastAPI

app = FastAPI(
    title="Bokking AI Scheduler",
    version="1.0",
    description="Async REST API for beauty salon booking with AI assistant",
)

@app.get("/")
async def root():
    return {"message": "Booking AI Scheduler API", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}