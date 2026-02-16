import logging
from fastapi import FastAPI
from app.config.config import config
from app.controllers.task_controller import router as task_router

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("Main")

app = FastAPI(
    title="Task Management API",
    description="API for creating and managing tasks",
    version="1.0.0"
)

app.include_router(task_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}