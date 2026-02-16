from fastapi import APIRouter, HTTPException
from app.domain.models.task import TaskCreate, Task
from app.services.task_service import TaskService

router = APIRouter()

# Dependency injection (for demo, instantiate here)
from app.repositories.task_repository import TaskRepository
task_service = TaskService(TaskRepository())

@router.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    try:
        return task_service.create_task(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))