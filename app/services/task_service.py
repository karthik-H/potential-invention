from app.domain.models.task import TaskCreate, Task
from app.repositories.task_repository import TaskRepository
import logging

class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository
        self.logger = logging.getLogger("TaskService")

    def create_task(self, task_data: TaskCreate) -> Task:
        self.logger.info(f"Creating task for user: {task_data.user_name}")
        return self.repository.add_task(task_data)