import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# --- Test Case 1: create_task_with_valid_data ---
def test_create_task_with_valid_data():
    data = {
        "title": "Buy groceries",
        "description": "Milk, Bread, Eggs",
        "due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == data["title"]
    assert resp["description"] == data["description"]
    assert resp["due_date"] == data["due_date"]
    assert resp["status"] == "pending"
    assert resp["id"]
    assert resp["created_at"]
    # ISO timestamp check (basic)
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", resp["created_at"])

# --- Test Case 2: create_task_missing_required_title ---
def test_create_task_missing_required_title():
    data = {
        "description": "Milk, Bread, Eggs",
        "due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert resp["detail"] == "Field 'title' is required"

# --- Test Case 3: create_task_with_empty_body ---
def test_create_task_with_empty_body():
    response = client.post("/tasks", json={})
    assert response.status_code == 422
    resp = response.json()
    assert resp["detail"] == "Field 'title' is required"

# --- Test Case 4: create_task_with_long_title ---
def test_create_task_with_long_title():
    long_title = "T" * 255
    data = {
        "title": long_title,
        "description": "Edge case test for long title",
        "due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == long_title
    assert resp["description"] == data["description"]
    assert resp["due_date"] == data["due_date"]
    assert resp["status"] == "pending"
    assert resp["id"]
    assert resp["created_at"]

# --- Test Case 5: create_task_with_title_exceeding_max_length ---
def test_create_task_with_title_exceeding_max_length():
    too_long_title = "T" * 256
    data = {
        "title": too_long_title,
        "description": "Overlong title",
        "due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert resp["detail"] == "Title must not exceed 255 characters"

# --- Test Case 6: create_task_with_invalid_due_date_format ---
def test_create_task_with_invalid_due_date_format():
    data = {
        "title": "Pay bills",
        "description": "Electricity and water",
        "due_date": "01-07-2024"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert resp["detail"] == "Invalid date format, expected YYYY-MM-DD"

# --- Test Case 7: create_task_without_content_type_header ---
def test_create_task_without_content_type_header():
    data = {
        "title": "Go running",
        "description": "Run 5km in the park",
        "due_date": "2024-07-01"
    }
    # Send as data, not json, and omit content-type
    response = client.post("/tasks", data=data)
    assert response.status_code == 415
    resp = response.json()
    assert resp["detail"] == "Unsupported Media Type"

# --- Test Case 8: create_task_with_unexpected_field ---
def test_create_task_with_unexpected_field():
    data = {
        "title": "Read book",
        "description": "Read 'Clean Code'",
        "due_date": "2024-07-01",
        "priority": "high"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 422
    resp = response.json()
    assert resp["detail"] == "Extra fields are not allowed: 'priority'"

# --- Test Case 9: create_task_with_minimal_required_fields ---
def test_create_task_with_minimal_required_fields():
    data = {
        "title": "Write tests"
    }
    response = client.post("/tasks", json=data)
    assert response.status_code == 201
    resp = response.json()
    assert resp["title"] == data["title"]
    assert resp["description"] is None
    assert resp["due_date"] is None
    assert resp["status"] == "pending"
    assert resp["id"]
    assert resp["created_at"]

# --- Test Case 10: create_task_with_duplicate_title ---
def test_create_task_with_duplicate_title():
    data = {
        "title": "Unique task"
    }
    # First creation
    response1 = client.post("/tasks", json=data)
    assert response1.status_code == 201
    resp1 = response1.json()
    assert resp1["title"] == data["title"]
    # Second creation (business rule: accept or reject, here we just check 201 or 409)
    response2 = client.post("/tasks", json=data)
    # Accept either 201 (allowed) or 409 (conflict), but must return a valid response
    assert response2.status_code in (201, 409)
    if response2.status_code == 201:
        resp2 = response2.json()
        assert resp2["title"] == data["title"]
    elif response2.status_code == 409:
        resp2 = response2.json()
        assert "detail" in resp2