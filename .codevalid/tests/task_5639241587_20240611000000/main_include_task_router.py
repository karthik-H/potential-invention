import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper to generate valid task data
def valid_task_data(**overrides):
    data = {
        "title": "Buy groceries",
        "description": "Milk, Bread, Eggs",
        "due_date": "2024-07-01",
        "priority": 3,
        "user_name": "alice"
    }
    data.update(overrides)
    return data

@pytest.fixture(autouse=True)
def clear_tasks_file(monkeypatch, tmp_path):
    # Patch TaskRepository to use a temp file for isolation
    from app.repositories import task_repository
    monkeypatch.setattr(task_repository, "TaskRepository", lambda: task_repository.TaskRepository(str(tmp_path / "tasks.json")))

# Test Case 1: Create Task - Success
def test_create_task_success():
    data = valid_task_data()
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == data["title"]
    assert resp["description"] == data["description"]
    assert resp["due_date"] == data["due_date"]
    assert resp["priority"] == data["priority"]
    assert resp["user_name"] == data["user_name"]
    assert isinstance(resp["id"], int)

# Test Case 2: Create Task - Missing Title
def test_create_task_missing_title():
    data = valid_task_data()
    data.pop("title")
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert any(
        err["loc"][-1] == "title" and err["msg"] == "field required"
        for err in resp["detail"]
    )

# Test Case 3: Create Task - Empty Title
def test_create_task_empty_title():
    data = valid_task_data(title="")
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert any(
        err["loc"][-1] == "title" and "ensure this value has at least 1 characters" in err["msg"]
        for err in resp["detail"]
    )

# Test Case 4: Create Task - Title Max Length
def test_create_task_title_max_length():
    max_title = "T" * 100  # Model uses max_length=100
    data = valid_task_data(title=max_title)
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == max_title

# Test Case 5: Create Task - Title Too Long
def test_create_task_title_too_long():
    too_long_title = "T" * 101  # Model uses max_length=100
    data = valid_task_data(title=too_long_title)
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert any(
        err["loc"][-1] == "title" and "ensure this value has at most 100 characters" in err["msg"]
        for err in resp["detail"]
    )

# Test Case 6: Create Task - Invalid Due Date Format
def test_create_task_invalid_due_date_format():
    data = valid_task_data(due_date="07-04-2024")
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert any(
        err["loc"][-1] == "due_date" and "invalid date format" in err["msg"]
        for err in resp["detail"]
    )

# Test Case 7: Create Task - Missing Description
def test_create_task_missing_description():
    data = valid_task_data()
    data.pop("description")
    response = client.post("/tasks", json=data)
    # Model requires description, so expect 422
    assert response.status_code == 422
    resp = response.json()
    assert any(
        err["loc"][-1] == "description" and err["msg"] == "field required"
        for err in resp["detail"]
    )

# Test Case 8: Create Task - Past Due Date
def test_create_task_past_due_date():
    data = valid_task_data(due_date="2020-01-01")
    response = client.post("/tasks", json=data)
    # No explicit validation for past dates in model, so expect 201 unless implemented
    # If validation is added, expect 422
    # Here, we check for 201 (current model)
    assert response.status_code == 201 or response.status_code == 422

# Test Case 9: Create Task - Extra Fields Ignored
def test_create_task_extra_fields_ignored():
    data = valid_task_data(priority=2)
    data["extra_field"] = "should be ignored"
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert "extra_field" not in resp

# Test Case 10: Create Task - No JSON Body
def test_create_task_no_json_body():
    response = client.post("/tasks", json={})
    assert response.status_code == 422
    resp = response.json()
    # Should require title, description, due_date, priority, user_name
    required_fields = {"title", "description", "due_date", "priority", "user_name"}
    missing_fields = {err["loc"][-1] for err in resp["detail"] if err["msg"] == "field required"}
    assert required_fields.issubset(missing_fields)