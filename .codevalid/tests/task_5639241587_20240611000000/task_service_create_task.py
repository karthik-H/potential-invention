import pytest
from unittest.mock import MagicMock, patch
from app.services.task_service import TaskService
from app.domain.models.task import TaskCreate
from app.repositories.task_repository import TaskRepository

@pytest.fixture
def mock_repository():
    return MagicMock(spec=TaskRepository)

@pytest.fixture
def service(mock_repository):
    return TaskService(repository=mock_repository)

def make_task_create(data):
    # Helper to create TaskCreate, filling missing fields with None if not present
    return TaskCreate(
        title=data.get("title"),
        description=data.get("description"),
        due_date=data.get("due_date"),
        priority=data.get("priority"),
    )

def test_create_task_with_valid_data(service, mock_repository):
    task_data = {
        "description": "Document the new API endpoints",
        "due_date": "2024-07-01",
        "priority": "high",
        "title": "Write documentation"
    }
    user_name = "alice"
    expected_result = {"success": True, "task_id": "generated_task_id"}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_missing_required_field(service, mock_repository):
    task_data = {
        "description": "Missing title field",
        "due_date": "2024-07-05",
        "priority": "medium"
    }
    user_name = "bob"
    expected_result = {"error": "Missing required field: title", "success": False}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_invalid_due_date(service, mock_repository):
    task_data = {
        "description": "The due_date is not in a valid format",
        "due_date": "07-01-2024",
        "priority": "low",
        "title": "Test invalid date"
    }
    user_name = "charlie"
    expected_result = {"error": "Invalid date format for due_date", "success": False}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_minimal_required_fields(service, mock_repository):
    task_data = {
        "title": "Minimal task"
    }
    user_name = "dana"
    expected_result = {"success": True, "task_id": "generated_task_id"}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_repository_failure(service, mock_repository):
    task_data = {
        "description": "Simulate repository.add_task throwing an exception",
        "title": "Test repo failure"
    }
    user_name = "eve"
    expected_result = {"error": "Database unavailable", "success": False}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.side_effect = Exception("Database unavailable")
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_long_title_and_description(service, mock_repository):
    long_title = "T" * 255
    long_description = "T" * 1024
    task_data = {
        "description": long_description,
        "due_date": "2024-12-31",
        "title": long_title
    }
    user_name = "frank"
    expected_result = {"success": True, "task_id": "generated_task_id"}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_empty_optional_fields(service, mock_repository):
    task_data = {
        "title": "No optional fields"
    }
    user_name = "grace"
    expected_result = {"success": True, "task_id": "generated_task_id"}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_invalid_priority(service, mock_repository):
    task_data = {
        "priority": "urgent",
        "title": "Invalid priority"
    }
    user_name = "harry"
    expected_result = {"error": "Invalid value for priority", "success": False}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result

def test_create_task_with_empty_title(service, mock_repository):
    task_data = {
        "title": ""
    }
    user_name = "isabel"
    expected_result = {"error": "Title cannot be empty", "success": False}

    with patch.object(service, "logger") as mock_logger:
        mock_repository.add_task.return_value = expected_result
        result = service.create_task(user_name=user_name, task_data=task_data)
        mock_logger.info.assert_any_call(f"Creation attempt for user: {user_name}")

    mock_repository.add_task.assert_called_once_with(task_data)
    assert result == expected_result