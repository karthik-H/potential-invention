import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def long_title(length):
    return "T" * length

@pytest.fixture(autouse=True)
def clear_tasks_file(monkeypatch, tmp_path):
    """
    Patch TaskRepository to use a temp file for each test, ensuring isolation.
    """
    from app.repositories import task_repository
    temp_file = tmp_path / "tasks.json"
    monkeypatch.setattr(task_repository, "TaskRepository", lambda: task_repository.TaskRepository(str(temp_file)))
    yield

def test_create_task_successfully():
    """
    Test Case 1: Create Task Successfully
    """
    data = {
        "title": "Finish documentation",
        "description": "Complete API docs for new endpoints",
        "priority": "high",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Finish documentation",
        "description": "Complete API docs for new endpoints",
        "priority": "high",
        "due_date": "2024-07-10",
        "status": "pending"
    }

def test_create_task_missing_title():
    """
    Test Case 2: Create Task Missing Title
    """
    data = {
        "description": "Task without title",
        "priority": "medium",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Title field is required"}

def test_create_task_with_empty_title():
    """
    Test Case 3: Create Task With Empty Title
    """
    data = {
        "title": "",
        "description": "Title is empty",
        "priority": "low",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Title cannot be empty"}

def test_create_task_missing_due_date():
    """
    Test Case 4: Create Task Missing Due Date
    """
    data = {
        "title": "Task without due date",
        "description": "Missing due date",
        "priority": "medium"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Due date field is required"}

def test_create_task_with_invalid_due_date_format():
    """
    Test Case 5: Create Task With Invalid Due Date Format
    """
    data = {
        "title": "Task with invalid date",
        "description": "Date is not valid",
        "priority": "medium",
        "due_date": "07-10-2024"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Due date must be in YYYY-MM-DD format"}

def test_create_task_with_boundary_priority_value():
    """
    Test Case 6: Create Task With Boundary Priority Value
    """
    data = {
        "title": "Low priority task",
        "description": "Check priority boundary",
        "priority": "low",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    assert response.json() == {
        "id": 2,
        "title": "Low priority task",
        "description": "Check priority boundary",
        "priority": "low",
        "due_date": "2024-07-10",
        "status": "pending"
    }

def test_create_task_with_invalid_priority_value():
    """
    Test Case 7: Create Task With Invalid Priority Value
    """
    data = {
        "title": "Invalid priority task",
        "description": "Priority not allowed",
        "priority": "urgent",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Priority value is invalid"}

def test_create_task_with_duplicate_title():
    """
    Test Case 8: Create Task With Duplicate Title
    """
    data1 = {
        "title": "Finish documentation",
        "description": "Complete API docs for new endpoints",
        "priority": "high",
        "due_date": "2024-07-10"
    }
    data2 = {
        "title": "Finish documentation",
        "description": "Duplicate task",
        "priority": "medium",
        "due_date": "2024-07-11"
    }
    response1 = client.post("/tasks", json=data1)
    assert response1.status_code == 201
    response2 = client.post("/tasks", json=data2)
    assert response2.status_code == 400
    assert response2.json() == {"detail": "Task with this title already exists"}

def test_create_task_with_maximum_length_title():
    """
    Test Case 9: Create Task With Maximum Length Title
    """
    max_title = long_title(255)
    data = {
        "title": max_title,
        "description": "Longest allowed title",
        "priority": "medium",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    assert response.json() == {
        "id": 3,
        "title": max_title,
        "description": "Longest allowed title",
        "priority": "medium",
        "due_date": "2024-07-10",
        "status": "pending"
    }

def test_create_task_with_title_exceeding_max_length():
    """
    Test Case 10: Create Task With Title Exceeding Max Length
    """
    too_long_title = long_title(256)
    data = {
        "title": too_long_title,
        "description": "Title exceeds max length",
        "priority": "medium",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Title exceeds maximum length of 255 characters"}

def test_create_task_without_description():
    """
    Test Case 11: Create Task Without Description
    """
    data = {
        "title": "Task without description",
        "priority": "medium",
        "due_date": "2024-07-10"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    assert response.json() == {
        "id": 4,
        "title": "Task without description",
        "description": None,
        "priority": "medium",
        "due_date": "2024-07-10",
        "status": "pending"
    }

def test_create_task_with_invalid_json_body():
    """
    Test Case 12: Create Task With Invalid JSON Body
    """
    invalid_json = '{"title": "Bad JSON", "description": "Malformed", "priority": "medium", "due_date": "2024-07-10"'  # missing closing }
    headers = {"Content-Type": "application/json"}
    response = client.post("/tasks", data=invalid_json, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid JSON payload"}

def test_create_task_with_future_due_date():
    """
    Test Case 13: Create Task With Future Due Date
    """
    data = {
        "title": "Future due date task",
        "description": "Due date in future",
        "priority": "medium",
        "due_date": "2099-12-31"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    assert response.json() == {
        "id": 5,
        "title": "Future due date task",
        "description": "Due date in future",
        "priority": "medium",
        "due_date": "2099-12-31",
        "status": "pending"
    }

def test_create_task_with_past_due_date():
    """
    Test Case 14: Create Task With Past Due Date
    """
    data = {
        "title": "Past due date task",
        "description": "Due date in past",
        "priority": "medium",
        "due_date": "2020-01-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Due date cannot be in the past"}