from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, alias='Title')
    description: str = Field(..., min_length=1, max_length=1000, alias='Description')
    priority: int = Field(..., ge=1, le=5, alias='Priority')
    due_date: date = Field(..., alias='Due_date')
    user_name: str = Field(..., min_length=1, max_length=50, alias='User_name')

    @validator('title')
    def title_must_not_contain_admin(cls, v):
        if 'ADMIN' in v.upper():
            raise ValueError('Task name must not contain ADMIN')
        return v

    class Config:
        # Allow population using both the field name (snake_case) and alias (PascalCase)
        allow_population_by_field_name = True


class Task(TaskCreate):
    id: int
