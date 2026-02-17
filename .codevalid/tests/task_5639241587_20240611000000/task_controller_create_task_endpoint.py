import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

# Utility for generating a long title
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

def test_create_task_with_valid_data():
    """
    Test Case 1: Create task with valid data
    """
    data = {
        "title": "Buy groceries",
        "description": "Buy milk, eggs, and bread",
        "priority": 2,
        "due_date": "2024-07-01",
        "user_name": "alice"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    expected = {
        "id": 1,
        "title": "Buy groceries",
        "description": "Buy milk, eggs, and bread",
        "priority": 2,
        "due_date": "2024-07-01",
        "status": "pending",
        "user_name": "alice"
    }
    resp_json = response.json()
    # The model may not include 'status', but the expected output does. Adjust if needed.
    for k, v in expected.items():
        assert resp_json[k] == v

def test_create_task_with_missing_title():
    """
    Test Case 2: Create task with missing title
    """
    data = {
        "description": "Complete assignment",
        "priority": 1,
        "due_date": "2024-07-05",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Title is required."} or "title" in response.json().get("detail", "").lower()

def test_create_task_with_empty_title():
    """
    Test Case 3: Create task with empty title
    """
    data = {
        "title": "",
        "description": "Do something important",
        "priority": 3,
        "due_date": "2024-07-10",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Title cannot be empty."} or "title" in response.json().get("detail", "").lower()

def test_create_task_with_invalid_due_date_format():
    """
    Test Case 4: Create task with invalid due_date format
    """
    data = {
        "title": "Submit report",
        "description": "Submit quarterly report",
        "priority": 2,
        "due_date": "31-07-2024",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "due_date must be in YYYY-MM-DD format."} or "due_date" in response.json().get("detail", "").lower()

def test_create_task_with_priority_out_of_bounds():
    """
    Test Case 5: Create task with priority out of bounds
    """
    data = {
        "title": "Pay bills",
        "description": "Pay electricity bill",
        "priority": -1,
        "due_date": "2024-07-15",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "priority must be between 1 and 5."} or "priority" in response.json().get("detail", "").lower()

def test_create_task_with_maximum_allowed_priority():
    """
    Test Case 6: Create task with maximum allowed priority
    """
    data = {
        "title": "Prepare presentation",
        "description": "Slides for annual meeting",
        "priority": 5,
        "due_date": "2024-07-20",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    expected = {
        "id": 1,
        "title": "Prepare presentation",
        "description": "Slides for annual meeting",
        "priority": 5,
        "due_date": "2024-07-20",
        "status": "pending",
        "user_name": "bob"
    }
    resp_json = response.json()
    for k, v in expected.items():
        assert resp_json[k] == v

def test_create_task_with_very_long_title():
    """
    Test Case 7: Create task with very long title
    """
    long_t = long_title(100)
    data = {
        "title": long_t,
        "description": "Description for long title",
        "priority": 3,
        "due_date": "2024-07-25",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    expected = {
        "id": 1,
        "title": long_t,
        "description": "Description for long title",
        "priority": 3,
        "due_date": "2024-07-25",
        "status": "pending",
        "user_name": "bob"
    }
    resp_json = response.json()
    for k, v in expected.items():
        assert resp_json[k] == v

def test_create_task_with_empty_description():
    """
    Test Case 8: Create task with empty description
    """
    data = {
        "title": "Call plumber",
        "description": "",
        "priority": 4,
        "due_date": "2024-07-30",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    expected = {
        "id": 1,
        "title": "Call plumber",
        "description": "",
        "priority": 4,
        "due_date": "2024-07-30",
        "status": "pending",
        "user_name": "bob"
    }
    resp_json = response.json()
    for k, v in expected.items():
        assert resp_json[k] == v

def test_create_task_with_invalid_json_body():
    """
    Test Case 9: Create task with invalid JSON body
    """
    invalid_json = '{"title": "Bad JSON", "description": "Malformed", "priority": 1, "due_date": "2024-07-10", "user_name": "bob"'  # missing closing }
    headers = {"Content-Type": "application/json"}
    response = client.post("/tasks", data=invalid_json, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Malformed JSON request body."} or "json" in response.json().get("detail", "").lower()

def test_create_task_with_duplicate_title():
    """
    Test Case 10: Create task with duplicate title
    """
    data1 = {
        "title": "Buy groceries",
        "description": "Buy milk, eggs, and bread",
        "priority": 2,
        "due_date": "2024-07-01",
        "user_name": "alice"
    }
    data2 = {
        "title": "Buy groceries",
        "description": "Buy vegetables",
        "priority": 2,
        "due_date": "2024-08-01",
        "user_name": "bob"
    }
    # Create first task
    response1 = client.post("/tasks", json=data1)
    assert response1.status_code == 201
    # Attempt duplicate
    response2 = client.post("/tasks", json=data2)
    assert response2.status_code == 400
    assert response2.json() == {"detail": "Task with this title already exists."} or "already exists" in response2.json().get("detail", "").lower()

def test_create_task_with_missing_content_type_header():
    """
    Test Case 11: Create task with missing Content-Type header
    """
    data = {
        "title": "Attend meeting",
        "description": "Team sync-up",
        "priority": 1,
        "due_date": "2024-08-02",
        "user_name": "bob"
    }
    # Send as data, not as json, and omit Content-Type
    response = client.post("/tasks", data=json.dumps(data))
    assert response.status_code == 400
    assert response.json() == {"detail": "Content-Type header must be application/json."} or "content-type" in response.json().get("detail", "").lower()