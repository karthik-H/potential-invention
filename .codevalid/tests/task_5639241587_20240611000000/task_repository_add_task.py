import os
import json
import tempfile
import pytest
import logging
from unittest import mock
from datetime import date

from app.repositories.task_repository import TaskRepository
from app.domain.models.task import Task, TaskCreate

# Helper to create TaskCreate with flexible fields
def make_task_create(**kwargs):
    base = {
        "title": "Default Title",
        "description": "Default Description",
        "priority": 2,
        "due_date": date.today(),
        "user_name": "default_user"
    }
    base.update(kwargs)
    return TaskCreate(**base)

@pytest.fixture
def temp_json_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
        yield tf.name
    if os.path.exists(tf.name):
        os.remove(tf.name)

@pytest.fixture(autouse=True)
def reset_logging():
    logging.getLogger("TaskRepository").handlers.clear()

def read_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def get_tasks_from_file(path):
    if not os.path.exists(path):
        return []
    try:
        data = read_json_file(path)
        return data.get("tasks", [])
    except Exception:
        return []

def get_id_counter_from_file(path):
    if not os.path.exists(path):
        return 1
    try:
        data = read_json_file(path)
        return data.get("id_counter", 1)
    except Exception:
        return 1

def get_log_records(caplog):
    return [r.getMessage() for r in caplog.records]

# Test Case 1: add_task_with_valid_input
def test_add_task_with_valid_input(temp_json_file, caplog):
    caplog.set_level(logging.INFO)
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    task_create = TaskCreate(
        title="Buy groceries",
        description="Milk, Bread, Eggs",
        priority=2,
        due_date=date(2024, 6, 30),
        user_name="alice"
    )
    created_task = repo.add_task(task_create)

    assert created_task.id == 1
    assert created_task.title == "Buy groceries"
    assert created_task.description == "Milk, Bread, Eggs"
    assert repo._id_counter == 2
    assert len(repo._tasks) == 1
    assert repo._tasks[0].id == 1

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][0]["id"] == 1
    assert file_data["tasks"][0]["title"] == "Buy groceries"
    assert file_data["id_counter"] == 2

    logs = get_log_records(caplog)
    assert any("Task created" in log for log in logs)

# Test Case 2: add_task_multiple_tasks
def test_add_task_multiple_tasks(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    # Pre-populate with two tasks
    task1 = Task(id=1, title="Task 1", description="Desc 1", priority=2, due_date=date(2024, 6, 1), user_name="user1")
    task2 = Task(id=2, title="Task 2", description="Desc 2", priority=2, due_date=date(2024, 6, 2), user_name="user2")
    repo._tasks = [task1, task2]
    repo._id_counter = 3
    write_json_file(temp_json_file, {
        "tasks": [task1.dict(), task2.dict()],
        "id_counter": 3
    })

    task_create = TaskCreate(
        title="Read book",
        description="Finish reading chapter 5",
        priority=2,
        due_date=date(2024, 6, 3),
        user_name="user3"
    )
    created_task = repo.add_task(task_create)

    assert created_task.id == 3
    assert created_task.title == "Read book"
    assert created_task.description == "Finish reading chapter 5"
    assert repo._id_counter == 4
    assert len(repo._tasks) == 3

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][2]["id"] == 3
    assert file_data["tasks"][2]["title"] == "Read book"
    assert file_data["id_counter"] == 4

# Test Case 3: add_task_missing_title
def test_add_task_missing_title(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    # description provided, title missing
    with pytest.raises(Exception) as excinfo:
        TaskCreate(description="Some description", priority=2, due_date=date(2024, 6, 30), user_name="bob")
    assert "title" in str(excinfo.value) or "field required" in str(excinfo.value)

    assert repo._id_counter == 1
    assert repo._tasks == []
    assert get_tasks_from_file(temp_json_file) == []

# Test Case 4: add_task_missing_description
def test_add_task_missing_description(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    task_create = TaskCreate(
        title="Finish homework",
        description=None,
        priority=2,
        due_date=date(2024, 6, 30),
        user_name="bob"
    )
    created_task = repo.add_task(task_create)

    assert created_task.id == 1
    assert created_task.title == "Finish homework"
    assert created_task.description is None
    assert repo._id_counter == 2
    assert len(repo._tasks) == 1

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][0]["id"] == 1
    assert file_data["tasks"][0]["title"] == "Finish homework"
    assert file_data["tasks"][0]["description"] is None

# Test Case 5: add_task_empty_title
def test_add_task_empty_title(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    with pytest.raises(Exception) as excinfo:
        TaskCreate(title="", description="Some description", priority=2, due_date=date(2024, 6, 30), user_name="bob")
    assert "title" in str(excinfo.value) or "empty" in str(excinfo.value)

    assert repo._id_counter == 1
    assert repo._tasks == []
    assert get_tasks_from_file(temp_json_file) == []

# Test Case 6: add_task_large_title_and_description
def test_add_task_large_title_and_description(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    large_title = "T" * 10000
    large_description = "D" * 10000

    task_create = TaskCreate(
        title=large_title,
        description=large_description,
        priority=2,
        due_date=date(2024, 8, 1),
        user_name="user5"
    )
    created_task = repo.add_task(task_create)

    assert created_task.title == large_title
    assert created_task.description == large_description
    assert created_task.id == 1
    assert repo._id_counter == 2

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][0]["title"] == large_title
    assert file_data["tasks"][0]["description"] == large_description

# Test Case 7: add_task_with_special_characters
def test_add_task_with_special_characters(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    special_title = "Test 🚀"
    special_description = "Description with 💡 and symbols #!@"

    task_create = TaskCreate(
        title=special_title,
        description=special_description,
        priority=2,
        due_date=date(2024, 8, 2),
        user_name="user6"
    )
    created_task = repo.add_task(task_create)

    assert created_task.title == special_title
    assert created_task.description == special_description
    assert created_task.id == 1
    assert repo._id_counter == 2

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][0]["title"] == special_title
    assert file_data["tasks"][0]["description"] == special_description

# Test Case 8: add_task_json_save_failure
def test_add_task_json_save_failure(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    task_create = TaskCreate(
        title="Save Failure Task",
        description="Testing JSON save error",
        priority=3,
        due_date=date(2024, 7, 15),
        user_name="user7"
    )

    with mock.patch.object(TaskRepository, "_save_data", side_effect=IOError("Disk full")):
        with pytest.raises(IOError):
            repo.add_task(task_create)

    # Task may be appended before save, but not persisted
    assert repo._id_counter == 2
    assert len(repo._tasks) == 1
    assert get_tasks_from_file(temp_json_file) == []

# Test Case 9: add_task_id_counter_corruption
def test_add_task_id_counter_corruption(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = "not-an-int"

    task_create = TaskCreate(
        title="Valid Title",
        description="Valid description",
        priority=2,
        due_date=date(2024, 7, 20),
        user_name="user8"
    )

    with pytest.raises(Exception) as excinfo:
        repo.add_task(task_create)
    assert "id" in str(excinfo.value) or "int" in str(excinfo.value) or "counter" in str(excinfo.value)

    assert get_tasks_from_file(temp_json_file) == []

# Test Case 10: add_task_duplicate_title
def test_add_task_duplicate_title(temp_json_file):
    # Pre-populate with one task
    initial_task = Task(
        id=1,
        title="Buy groceries",
        description="First instance",
        priority=2,
        due_date=date(2024, 6, 22),
        user_name="user1"
    )
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = [initial_task]
    repo._id_counter = 2
    write_json_file(temp_json_file, {
        "tasks": [initial_task.dict()],
        "id_counter": 2
    })

    task_create = TaskCreate(
        title="Buy groceries",
        description="New description",
        priority=2,
        due_date=date(2024, 7, 1),
        user_name="user2"
    )
    created_task = repo.add_task(task_create)

    assert created_task.id == 2
    assert created_task.title == "Buy groceries"
    assert created_task.description == "New description"
    assert repo._id_counter == 3
    assert len(repo._tasks) == 2

    file_data = read_json_file(temp_json_file)
    assert len(file_data["tasks"]) == 2
    assert file_data["tasks"][1]["id"] == 2
    assert file_data["tasks"][1]["title"] == "Buy groceries"

# Test Case 11: add_task_with_minimal_fields
def test_add_task_with_minimal_fields(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    # Only required field: title
    task_create = TaskCreate(
        title="Short Task",
        description=None,
        priority=2,
        due_date=date(2024, 8, 10),
        user_name="user10"
    )
    created_task = repo.add_task(task_create)

    assert created_task.id == 1
    assert created_task.title == "Short Task"
    assert created_task.description is None
    assert repo._id_counter == 2
    assert len(repo._tasks) == 1

    file_data = read_json_file(temp_json_file)
    assert file_data["tasks"][0]["id"] == 1
    assert file_data["tasks"][0]["title"] == "Short Task"

# Test Case 12: add_task_logging_on_success
def test_add_task_logging_on_success(temp_json_file, caplog):
    caplog.set_level(logging.INFO)
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    task_create = TaskCreate(
        title="Log Test",
        description="Should log creation",
        priority=2,
        due_date=date(2024, 8, 11),
        user_name="user11"
    )
    created_task = repo.add_task(task_create)

    logs = get_log_records(caplog)
    assert any("Task created" in log for log in logs)

# Test Case 13: add_task_logging_failure
def test_add_task_logging_failure(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    task_create = TaskCreate(
        title="Logging Failure",
        description="Logger will fail",
        priority=2,
        due_date=date(2024, 8, 12),
        user_name="user12"
    )

    # Patch logger to raise exception on info
    with mock.patch("logging.Logger.info", side_effect=Exception("Logging failed")):
        created_task = repo.add_task(task_create)
        assert created_task.id == 1
        assert repo._id_counter == 2
        assert len(repo._tasks) == 1

        file_data = read_json_file(temp_json_file)
        assert file_data["tasks"][0]["id"] == 1

# Test Case 14: add_task_input_type_validation
def test_add_task_input_type_validation(temp_json_file):
    repo = TaskRepository(data_file=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1

    # Title is integer (invalid)
    with pytest.raises(Exception) as excinfo:
        TaskCreate(title=12345, description="Valid description", priority=2, due_date=date(2024, 8, 13), user_name="user13")
    assert "title" in str(excinfo.value) or "str type" in str(excinfo.value) or "not a valid string" in str(excinfo.value)

    assert repo._id_counter == 1
    assert repo._tasks == []
    assert get_tasks_from_file(temp_json_file) == []
