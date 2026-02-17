import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.models.task import Task, TaskCreate
from app.services.task_service import TaskService
from app.repositories.task_repository import TaskRepository
from datetime import date

client = TestClient(app)

# Helper to generate long strings
def repeat(char, count):
    return char * count

@pytest.fixture
def task_service(tmp_path):
    # Use a temp file for the repository to avoid polluting real data
    repo = TaskRepository(data_file=str(tmp_path / "tasks.json"))
    return TaskService(repo)

def test_create_task_success_all_fields_present(task_service):
    data = {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "priority": 3,
        "due_date": "2024-07-01",
        "user_name": "alice"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == data["title"]
    assert resp["description"] == data["description"]
    assert resp["priority"] == data["priority"]
    assert resp["due_date"] == data["due_date"]
    assert resp["user_name"] == data["user_name"]
    assert "id" in resp

def test_create_task_missing_title(task_service):
    data = {
        "description": "Call mom",
        "priority": 2,
        "due_date": "2024-07-01",
        "user_name": "bob"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    # FastAPI returns 422 for validation errors by default
    if response.status_code == 422:
        assert "title" in str(response.json())
    else:
        assert "title" in response.json().get("error", "")

def test_create_task_missing_multiple_fields(task_service):
    data = {
        "priority": 1,
        "due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    if response.status_code == 422:
        # FastAPI validation error
        assert "title" in str(response.json())
        assert "description" in str(response.json())
        assert "user_name" in str(response.json())
    else:
        err = response.json().get("error", "")
        assert "title" in err
        assert "description" in err
        assert "user_name" in err

def test_create_task_empty_string_fields(task_service):
    data = {
        "title": "",
        "description": "",
        "priority": 4,
        "due_date": "2024-07-01",
        "user_name": ""
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    if response.status_code == 422:
        # FastAPI validation error
        assert "title" in str(response.json())
        assert "description" in str(response.json())
        assert "user_name" in str(response.json())
    else:
        err = response.json().get("error", "")
        assert "title" in err
        assert "description" in err
        assert "user_name" in err

def test_create_task_invalid_due_date_format(task_service):
    data = {
        "title": "Finish homework",
        "description": "Math and Science",
        "priority": 2,
        "due_date": "07-01-2024",  # Invalid format
        "user_name": "charlie"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    if response.status_code == 422:
        # FastAPI validation error
        assert "due_date" in str(response.json())
    else:
        assert "due_date" in response.json().get("error", "")

def test_create_task_priority_boundary_value(task_service):
    data = {
        "title": "Read book",
        "description": "Read 'Clean Code'",
        "priority": 1,  # boundary value (min)
        "due_date": "2024-07-01",
        "user_name": "dave"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == data["title"]
    assert resp["description"] == data["description"]
    assert resp["priority"] == data["priority"]
    assert resp["due_date"] == data["due_date"]
    assert resp["user_name"] == data["user_name"]
    assert "id" in resp

def test_create_task_long_title_description(task_service):
    long_title = repeat("T", 100)
    long_desc = repeat("D", 1000)
    data = {
        "title": long_title,
        "description": long_desc,
        "priority": 5,
        "due_date": "2024-07-01",
        "user_name": "eve"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == long_title
    assert resp["description"] == long_desc
    assert resp["priority"] == data["priority"]
    assert resp["due_date"] == data["due_date"]
    assert resp["user_name"] == data["user_name"]
    assert "id" in resp

def test_create_task_duplicate_title_for_user(task_service):
    # Create first task
    data1 = {
        "title": "Walk dog",
        "description": "Morning walk",
        "priority": 2,
        "due_date": "2024-06-30",
        "user_name": "frank"
    }
    response1 = client.post("/tasks", json=data1)
    assert response1.status_code == 201
    # Create second task with same title for same user
    data2 = {
        "title": "Walk dog",
        "description": "Evening walk",
        "priority": 3,
        "due_date": "2024-07-01",
        "user_name": "frank"
    }
    response2 = client.post("/tasks", json=data2)
    assert response2.status_code == 201
    resp = response2.json()
    assert resp["title"] == data2["title"]
    assert resp["description"] == data2["description"]
    assert resp["priority"] == data2["priority"]
    assert resp["due_date"] == data2["due_date"]
    assert resp["user_name"] == data2["user_name"]
    assert "id" in resp

def test_create_task_missing_request_body(task_service):
    data = {}
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    if response.status_code == 422:
        # FastAPI validation error
        for field in ["title", "description", "priority", "due_date", "user_name"]:
            assert field in str(response.json())
    else:
        err = response.json().get("error", "")
        for field in ["title", "description", "priority", "due_date", "user_name"]:
            assert field in err

def test_create_task_invalid_priority_value(task_service):
    data = {
        "title": "Test invalid priority",
        "description": "Should fail",
        "priority": 10,  # Invalid value
        "due_date": "2024-07-01",
        "user_name": "grace"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422 or response.status_code == 400
    if response.status_code == 422:
        # FastAPI validation error
        assert "priority" in str(response.json())
    else:
        assert "priority" in response.json().get("error", "")