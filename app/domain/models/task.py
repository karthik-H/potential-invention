from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    priority: int = Field(..., ge=1, le=5)
    due_date: date
    user_name: str = Field(..., min_length=1, max_length=50)


class Task(TaskCreate):
    id: int