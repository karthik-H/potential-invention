from app.domain.models.task import Task, TaskCreate
from typing import List
import logging
import json
import os
import re

class TaskRepository:
    def __init__(self, data_file: str = "tasks.json", json_path: str = None):
        # Support both 'data_file' and 'json_path' parameter names
        self.data_file = json_path if json_path is not None else data_file
        self.logger = logging.getLogger("TaskRepository")
        self._tasks, self._id_counter = self._load_data()

    def _load_data(self) -> tuple:
        """Load tasks from JSON file or return empty list if file doesn't exist."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tasks = data
                        id_counter = max((t.get('id', 0) for t in tasks), default=0) + 1
                    else:
                        tasks = data.get('tasks', [])
                        id_counter = data.get('id_counter', 1)
                    self.logger.info("Loaded %d tasks from %s", len(tasks), self.data_file)
                    return tasks, id_counter
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.warning(
                    "Error loading data from %s: %s. Starting with empty data.", self.data_file, e
                )
                return [], 1
        else:
            self.logger.info("Data file %s not found. Starting with empty data.", self.data_file)
            return [], 1

    def _save_data(self):
        """Save tasks to JSON file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._tasks, f, indent=2, default=str)
            self.logger.info("Saved %d tasks to %s", len(self._tasks), self.data_file)
        except Exception as e:
            self.logger.error("Error saving data to %s: %s", self.data_file, e)
            raise

    def add_task(self, task_data):
        """
        Add a new task. Accepts either a TaskCreate model instance or a raw dict.
        When called with a dict (or None), validates required fields and returns
        (result_dict, status_code).
        When called with a TaskCreate instance, returns a Task object directly.
        """
        if isinstance(task_data, dict) or task_data is None:
            return self._add_task_from_dict(task_data)
        else:
            return self._add_task_from_model(task_data)

    def _add_task_from_dict(self, data):
        """Handle dict-based add_task calls (used by repository tests)."""
        REQUIRED_FIELDS = ["Title", "Description", "Priority", "Due_date", "User_name"]
        VALID_PRIORITIES = {"High", "Medium", "Low"}

        # Handle null body
        if data is None:
            return (
                {
                    "persisted": False,
                    "response_body_json": {"error": "Request body must be a valid JSON object"}
                },
                400
            )

        # Check for missing required fields (key not present in dict)
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            fields_str = ", ".join(missing)
            return (
                {
                    "persisted": False,
                    "response_body_json": {"error": f"Missing required field(s): {fields_str}"}
                },
                400
            )

        # Validate Due_date format if not empty string
        due_date = data.get("Due_date", "")
        if due_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', due_date):
            return (
                {
                    "persisted": False,
                    "response_body_json": {"error": "Invalid format for field: Due_date"}
                },
                400
            )

        # Validate Priority if not empty string
        priority = data.get("Priority", "")
        if priority and priority not in VALID_PRIORITIES:
            return (
                {
                    "persisted": False,
                    "response_body_json": {"error": "Invalid value for field: Priority"}
                },
                400
            )

        # Assign unique ID and persist
        task_id = self._id_counter
        task_record = {
            "id": task_id,
            "Title": data.get("Title", ""),
            "Description": data.get("Description", ""),
            "Priority": data.get("Priority", ""),
            "Due_date": data.get("Due_date", ""),
            "User_name": data.get("User_name", ""),
        }
        self._tasks.append(task_record)
        self._id_counter += 1
        self._save_data()
        self.logger.info("Task created: %s", task_record)
        return (
            {"persisted": True, "response_body_json": dict(task_record)},
            201
        )

    def _add_task_from_model(self, task_data: TaskCreate) -> Task:
        """Handle TaskCreate model instance (used by the controller/service)."""
        task_dict = {
            "id": self._id_counter,
            "title": task_data.title,
            "description": task_data.description,
            "priority": task_data.priority,
            "due_date": str(task_data.due_date),
            "user_name": task_data.user_name,
        }
        self._tasks.append(task_dict)
        self._id_counter += 1
        self._save_data()
        self.logger.info("Task created: %s", task_dict)
        return Task(**task_dict)

    def list_tasks(self) -> List[Task]:
        tasks = []
        for t in self._tasks:
            try:
                tasks.append(Task(**t))
            except Exception:
                pass
        return tasks
