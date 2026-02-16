from app.domain.models.task import Task, TaskCreate
from typing import List
import logging
import json
import os

class TaskRepository:
    def __init__(self, data_file: str = "tasks.json"):
        self.data_file = data_file
        self.logger = logging.getLogger("TaskRepository")
        self._tasks, self._id_counter = self._load_data()

    def _load_data(self) -> tuple[List[Task], int]:
        """Load tasks from JSON file or return empty list if file doesn't exist."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks = [Task(**task_dict) for task_dict in data.get('tasks', [])]
                    id_counter = data.get('id_counter', 1)
                    self.logger.info("Loaded %d tasks from %s", len(tasks), self.data_file)
                    return tasks, id_counter
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.warning("Error loading data from %s: %s. Starting with empty data.", self.data_file, e)
                return [], 1
        else:
            self.logger.info("Data file %s not found. Starting with empty data.", self.data_file)
            return [], 1

    def _save_data(self):
        """Save tasks to JSON file."""
        try:
            data = {
                'tasks': [task.dict() for task in self._tasks],
                'id_counter': self._id_counter
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info("Saved %d tasks to %s", len(self._tasks), self.data_file)
        except Exception as e:
            self.logger.error("Error saving data to %s: %s", self.data_file, e)
            raise

    def add_task(self, task_data: TaskCreate) -> Task:
        task = Task(id=self._id_counter, **task_data.dict())
        self._tasks.append(task)
        self._id_counter += 1
        self._save_data()
        self.logger.info("Task created: %s", task)
        return task

    def list_tasks(self) -> List[Task]:
        return self._tasks