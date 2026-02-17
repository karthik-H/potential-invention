import os
import json
import pytest
from datetime import datetime

from app.repositories.task_repository import TaskRepository
from app.domain.models.task import Task

import tempfile
import shutil

@pytest.fixture
def temp_json_file():
    # Create a temporary directory and file for the JSON DB
    temp_dir = tempfile.mkdtemp()
    json_path = os.path.join(temp_dir, "tasks.json")
    # Start with an empty list
    with open(json_path, "w") as f:
        json.dump([], f)
    yield json_path
    shutil.rmtree(temp_dir)

@pytest.fixture
def repo(temp_json_file):
    # Patch the repository to use the temp file and reset id counter
    repo = TaskRepository(json_path=temp_json_file)
    repo._tasks = []
    repo._id_counter = 1
    return repo

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_json_tasks(json_path):
    with open(json_path, "r") as f:
        return json.load(f)

# Test Case 1: Add Task with All Required Fields
def test_add_task_with_all_required_fields(repo, temp_json_file):
    data = {
        "Description": "Milk, eggs, bread",
        "Due_date": "2024-07-01",
        "Priority": "High",
        "Title": "Buy groceries",
        "User_name": "alice"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Description"] == data["Description"]
    assert resp["Due_date"] == data["Due_date"]
    assert resp["Priority"] == data["Priority"]
    assert resp["Title"] == data["Title"]
    assert resp["User_name"] == data["User_name"]
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == "Buy groceries" for t in tasks)

# Test Case 2: Add Task Missing Title
def test_add_task_missing_title(repo):
    data = {
        "Description": "Read a book",
        "Due_date": "2024-07-02",
        "Priority": "Medium",
        "User_name": "bob"
    }
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    assert result["response_body_json"]["error"] == "Missing required field(s): Title"

# Test Case 3: Add Task Missing Multiple Required Fields
def test_add_task_missing_multiple_required_fields(repo):
    data = {
        "Priority": "Low",
        "Title": "Walk dog"
    }
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    err = result["response_body_json"]["error"]
    # Order of fields may vary
    missing = set(err.replace("Missing required field(s): ", "").replace(" ", "").split(","))
    assert missing == {"Description", "Due_date", "User_name"}

# Test Case 4: Add Task with Empty Strings in Fields
def test_add_task_with_empty_strings_in_fields(repo, temp_json_file):
    data = {
        "Description": "",
        "Due_date": "",
        "Priority": "",
        "Title": "",
        "User_name": ""
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Description"] == ""
    assert resp["Due_date"] == ""
    assert resp["Priority"] == ""
    assert resp["Title"] == ""
    assert resp["User_name"] == ""
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == "" and t["Description"] == "" for t in tasks)

# Test Case 5: Add Task with Invalid Due Date Format
def test_add_task_with_invalid_due_date_format(repo):
    data = {
        "Description": "Complete all modules",
        "Due_date": "07-01-2024",
        "Priority": "High",
        "Title": "Finish project",
        "User_name": "charlie"
    }
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    assert result["response_body_json"]["error"] == "Invalid format for field: Due_date"

# Test Case 6: Add Task with Long Title and Description
def test_add_task_with_long_title_and_description(repo, temp_json_file):
    long_desc = "D" * 1024
    long_title = "T" * 255
    data = {
        "Description": long_desc,
        "Due_date": "2024-07-03",
        "Priority": "Medium",
        "Title": long_title,
        "User_name": "dave"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Description"] == long_desc
    assert resp["Title"] == long_title
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == long_title and t["Description"] == long_desc for t in tasks)

# Test Case 7: Add Task Ensures Unique ID Assignment
def test_add_task_ensures_unique_id_assignment(repo):
    data1 = {
        "Description": "First task",
        "Due_date": "2024-07-04",
        "Priority": "Low",
        "Title": "Task 1",
        "User_name": "eve"
    }
    data2 = {
        "Description": "Second task",
        "Due_date": "2024-07-05",
        "Priority": "High",
        "Title": "Task 2",
        "User_name": "eve"
    }
    result1, status1 = repo.add_task(data1)
    result2, status2 = repo.add_task(data2)
    assert status1 == 201
    assert status2 == 201
    id1 = result1["response_body_json"]["id"]
    id2 = result2["response_body_json"]["id"]
    assert id1 != id2
    assert int(id2) == int(id1) + 1
    assert result1["persisted"] is True
    assert result2["persisted"] is True

# Test Case 8: Add Task with Minimum Priority Value
def test_add_task_with_minimum_priority_value(repo, temp_json_file):
    data = {
        "Description": "Wash and fold clothes",
        "Due_date": "2024-07-06",
        "Priority": "Low",
        "Title": "Do laundry",
        "User_name": "frank"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Priority"] == "Low"
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == "Do laundry" for t in tasks)

# Test Case 9: Add Task with Maximum Priority Value
def test_add_task_with_maximum_priority_value(repo, temp_json_file):
    data = {
        "Description": "Resolve critical bug",
        "Due_date": "2024-07-07",
        "Priority": "High",
        "Title": "Urgent fix",
        "User_name": "gina"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Priority"] == "High"
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == "Urgent fix" for t in tasks)

# Test Case 10: Add Task with Invalid Priority Value
def test_add_task_with_invalid_priority_value(repo):
    data = {
        "Description": "Testing invalid priority",
        "Due_date": "2024-07-08",
        "Priority": "Urgent",
        "Title": "Invalid priority task",
        "User_name": "hank"
    }
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    assert result["response_body_json"]["error"] == "Invalid value for field: Priority"

# Test Case 11: Add Task with Empty Request Body
def test_add_task_with_empty_request_body(repo):
    data = {}
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    err = result["response_body_json"]["error"]
    missing = set(err.replace("Missing required field(s): ", "").replace(" ", "").split(","))
    assert missing == {"Title", "Description", "Priority", "Due_date", "User_name"}

# Test Case 12: Add Task with Null Request Body
def test_add_task_with_null_request_body(repo):
    data = None
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    assert result["response_body_json"]["error"] == "Request body must be a valid JSON object"

# Test Case 13: Add Task with Due Date as Today's Date
def test_add_task_with_due_date_as_today(repo, temp_json_file):
    today = get_today_date()
    data = {
        "Description": "Complete today",
        "Due_date": today,
        "Priority": "Medium",
        "Title": "Today's task",
        "User_name": "iris"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Due_date"] == today
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Due_date"] == today and t["Title"] == "Today's task" for t in tasks)

# Test Case 14: Add Task and Verify Persistence to JSON
def test_add_task_and_verify_persistence_to_json(repo, temp_json_file):
    data = {
        "Description": "Check JSON file",
        "Due_date": "2024-07-09",
        "Priority": "Low",
        "Title": "Persist test",
        "User_name": "jack"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Title"] == "Persist test"
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == "Persist test" and t["User_name"] == "jack" for t in tasks)

# Test Case 15: Add Task Missing User_name
def test_add_task_missing_user_name(repo):
    data = {
        "Description": "Read the new science article",
        "Due_date": "2024-07-10",
        "Priority": "Medium",
        "Title": "Read article"
    }
    result, status = repo.add_task(data)
    assert status == 400
    assert result["persisted"] is False
    assert result["response_body_json"]["error"] == "Missing required field(s): User_name"

# Test Case 16: Add Task with Special Characters in Fields
def test_add_task_with_special_characters_in_fields(repo, temp_json_file):
    data = {
        "Description": "Description with emoji 😊🚀",
        "Due_date": "2024-07-11",
        "Priority": "High",
        "Title": "@#$$%^&*()_+",
        "User_name": "user!@#"
    }
    result, status = repo.add_task(data)
    assert status == 201
    assert result["persisted"] is True
    resp = result["response_body_json"]
    assert resp["Description"] == data["Description"]
    assert resp["Title"] == data["Title"]
    assert resp["User_name"] == data["User_name"]
    assert "id" in resp
    # Check JSON file
    tasks = get_json_tasks(temp_json_file)
    assert any(t["Title"] == data["Title"] and t["Description"] == data["Description"] for t in tasks)