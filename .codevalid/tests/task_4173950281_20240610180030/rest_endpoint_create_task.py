import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Helper to generate a string of a given length
def make_str(length):
    return "T" * length

@pytest.mark.parametrize("payload,expected_status,expected_body", [
    # Test Case 1: Create Task with All Required Fields
    (
        {
            "Title": "Buy groceries",
            "Description": "Buy milk, eggs, and bread",
            "Priority": 2,
            "Due_date": "2024-07-01",
            "User_name": "johndoe"
        },
        201,
        {
            "Title": "Buy groceries",
            "Description": "Buy milk, eggs, and bread",
            "Priority": 2,
            "Due_date": "2024-07-01",
            "User_name": "johndoe"
            # id will be checked separately
        }
    ),
])
def test_create_task_with_all_required_fields(payload, expected_status, expected_body):
    response = client.post("/tasks", json=payload)
    assert response.status_code == expected_status
    data = response.json()
    for k, v in expected_body.items():
        assert data[k] == v
    assert "id" in data
    assert isinstance(data["id"], int)

def test_create_task_missing_title():
    payload = {
        "Description": "Buy milk, eggs, and bread",
        "Priority": 2,
        "Due_date": "2024-07-01",
        "User_name": "johndoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert {"loc": ["body", "Title"], "msg": "field required", "type": "value_error.missing"} in data["detail"]

def test_create_task_missing_description():
    payload = {
        "Title": "Buy groceries",
        "Priority": 2,
        "Due_date": "2024-07-01",
        "User_name": "johndoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert {"loc": ["body", "Description"], "msg": "field required", "type": "value_error.missing"} in data["detail"]

def test_create_task_missing_priority():
    payload = {
        "Title": "Buy groceries",
        "Description": "Buy milk, eggs, and bread",
        "Due_date": "2024-07-01",
        "User_name": "johndoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert {"loc": ["body", "Priority"], "msg": "field required", "type": "value_error.missing"} in data["detail"]

def test_create_task_missing_due_date():
    payload = {
        "Title": "Buy groceries",
        "Description": "Buy milk, eggs, and bread",
        "Priority": 2,
        "User_name": "johndoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert {"loc": ["body", "Due_date"], "msg": "field required", "type": "value_error.missing"} in data["detail"]

def test_create_task_missing_user_name():
    payload = {
        "Title": "Buy groceries",
        "Description": "Buy milk, eggs, and bread",
        "Priority": 2,
        "Due_date": "2024-07-01"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert {"loc": ["body", "User_name"], "msg": "field required", "type": "value_error.missing"} in data["detail"]

def test_create_task_missing_multiple_fields():
    payload = {
        "Title": "Buy groceries",
        "Priority": 2
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    expected = [
        {"loc": ["body", "Description"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "Due_date"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "User_name"], "msg": "field required", "type": "value_error.missing"},
    ]
    for err in expected:
        assert err in data["detail"]

def test_create_task_invalid_due_date_format():
    payload = {
        "Title": "Pay bills",
        "Description": "Pay electricity and water bills",
        "Priority": 1,
        "Due_date": "31-07-2024",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    found = False
    for err in data["detail"]:
        if err["loc"] == ["body", "Due_date"] and "date" in err["type"]:
            found = True
    assert found

def test_create_task_non_integer_priority():
    payload = {
        "Title": "Meeting",
        "Description": "Discuss project",
        "Priority": "high",
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    found = False
    for err in data["detail"]:
        if err["loc"] == ["body", "Priority"] and err["type"] == "type_error.integer":
            found = True
    assert found

def test_create_task_empty_title():
    payload = {
        "Title": "",
        "Description": "Task with empty title",
        "Priority": 2,
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    found = False
    for err in data["detail"]:
        if err["loc"] == ["body", "Title"] and "min_length" in err["type"]:
            found = True
    assert found

def test_create_task_max_title_length():
    payload = {
        "Title": make_str(100),
        "Description": "Test max title length",
        "Priority": 2,
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Title"] == make_str(100)
    assert data["Description"] == "Test max title length"
    assert data["Priority"] == 2
    assert data["Due_date"] == "2024-07-01"
    assert data["User_name"] == "janedoe"
    assert "id" in data

def test_create_task_title_exceeding_max_length():
    payload = {
        "Title": make_str(101),
        "Description": "Test title exceeding max length",
        "Priority": 1,
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    found = False
    for err in data["detail"]:
        if err["loc"] == ["body", "Title"] and "max_length" in err["type"]:
            found = True
    assert found

def test_create_task_min_priority_value():
    payload = {
        "Title": "Low priority task",
        "Description": "Test with minimum priority",
        "Priority": 1,
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Priority"] == 1

def test_create_task_priority_below_minimum():
    payload = {
        "Title": "Negative priority task",
        "Description": "Test with negative priority",
        "Priority": 0,
        "Due_date": "2024-07-01",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    found = False
    for err in data["detail"]:
        if err["loc"] == ["body", "Priority"] and "not_ge" in err["type"]:
            found = True
    assert found

def test_create_task_due_date_today():
    payload = {
        "Title": "Task due today",
        "Description": "Test with due date as today",
        "Priority": 2,
        "Due_date": "2024-06-10",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Due_date"] == "2024-06-10"

def test_create_task_due_date_in_past():
    payload = {
        "Title": "Past due task",
        "Description": "Task with past due date",
        "Priority": 2,
        "Due_date": "2023-12-31",
        "User_name": "janedoe"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Due_date"] == "2023-12-31"

def test_create_task_empty_request_body():
    payload = {}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 400
    data = response.json()
    expected = [
        {"loc": ["body", "Title"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "Description"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "Priority"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "Due_date"], "msg": "field required", "type": "value_error.missing"},
        {"loc": ["body", "User_name"], "msg": "field required", "type": "value_error.missing"},
    ]
    for err in expected:
        assert err in data["detail"]

def test_create_task_with_extra_fields():
    payload = {
        "Title": "Task with extra field",
        "Description": "Test extra field",
        "Priority": 2,
        "Due_date": "2024-07-01",
        "User_name": "janedoe",
        "ExtraField": "should be ignored"
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["Title"] == "Task with extra field"
    assert data["Description"] == "Test extra field"
    assert data["Priority"] == 2
    assert data["Due_date"] == "2024-07-01"
    assert data["User_name"] == "janedoe"
    assert "id" in data