import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from pydantic import ValidationError

from app.services.task_service import TaskService
from app.domain.models.task import TaskCreate, Task
from app.repositories.task_repository import TaskRepository

@pytest.fixture
def mock_repository():
    repo = MagicMock(spec=TaskRepository)
    return repo

@pytest.fixture
def service(mock_repository):
    return TaskService(repository=mock_repository)

@pytest.fixture
def valid_task_data():
    return TaskCreate(
        title="Test Task",
        description="A test description.",
        priority=3,
        due_date=date.today() + timedelta(days=1),
        user_name="testuser"
    )

def test_create_task_with_valid_data(service, mock_repository, valid_task_data):
    expected_task = Task(id=1, **valid_task_data.dict())
    mock_repository.add_task.return_value = expected_task

    with patch.object(service.logger, "info") as mock_log:
        result = service.create_task(valid_task_data)

    mock_repository.add_task.assert_called_once_with(valid_task_data)
    mock_log.assert_any_call(f"Creating task for user: {valid_task_data.user_name}")
    assert result == expected_task

def test_create_task_missing_title(service, mock_repository, valid_task_data):
    invalid_data = valid_task_data.copy(update={"title": ""})
    with pytest.raises(ValidationError):
        TaskCreate(**{**valid_task_data.dict(), "title": ""})

def test_create_task_empty_description(service, mock_repository, valid_task_data):
    # description min_length=1, so empty string should fail validation
    with pytest.raises(ValidationError):
        TaskCreate(**{**valid_task_data.dict(), "description": ""})

def test_create_task_invalid_due_date_format(service, mock_repository, valid_task_data):
    # due_date must be a date, so passing a string should fail
    with pytest.raises(ValidationError):
        TaskCreate(**{**valid_task_data.dict(), "due_date": "not-a-date"})

def test_create_task_with_null_user_name(service, mock_repository, valid_task_data):
    # user_name min_length=1, so None or "" should fail validation
    with pytest.raises(ValidationError):
        TaskCreate(**{**valid_task_data.dict(), "user_name": None})

def test_create_task_min_title_length(service, mock_repository, valid_task_data):
    min_title = "A"
    data = valid_task_data.copy(update={"title": min_title})
    expected_task = Task(id=1, **data.dict())
    mock_repository.add_task.return_value = expected_task

    with patch.object(service.logger, "info") as mock_log:
        result = service.create_task(data)

    mock_repository.add_task.assert_called_once_with(data)
    mock_log.assert_any_call(f"Creating task for user: {data.user_name}")
    assert result == expected_task

def test_create_task_max_title_length(service, mock_repository, valid_task_data):
    max_title = "T" * 100  # max_length=100
    data = valid_task_data.copy(update={"title": max_title})
    expected_task = Task(id=1, **data.dict())
    mock_repository.add_task.return_value = expected_task

    with patch.object(service.logger, "info") as mock_log:
        result = service.create_task(data)

    mock_repository.add_task.assert_called_once_with(data)
    mock_log.assert_any_call(f"Creating task for user: {data.user_name}")
    assert result == expected_task

def test_create_task_repository_failure(service, mock_repository, valid_task_data):
    mock_repository.add_task.side_effect = Exception("Repository failure")
    with patch.object(service.logger, "info") as mock_log:
        with pytest.raises(Exception, match="Repository failure"):
            service.create_task(valid_task_data)
    mock_log.assert_any_call(f"Creating task for user: {valid_task_data.user_name}")

def test_create_task_duplicate_task(service, mock_repository, valid_task_data):
    # Simulate repository raising an exception for duplicate
    mock_repository.add_task.side_effect = Exception("Duplicate task")
    with patch.object(service.logger, "info") as mock_log:
        with pytest.raises(Exception, match="Duplicate task"):
            service.create_task(valid_task_data)
    mock_log.assert_any_call(f"Creating task for user: {valid_task_data.user_name}")

def test_create_task_special_characters_in_title(service, mock_repository, valid_task_data):
    special_title = "Task!@#$%^&*()_+-=[]{}|;':,.<>/?"
    data = valid_task_data.copy(update={"title": special_title})
    expected_task = Task(id=1, **data.dict())
    mock_repository.add_task.return_value = expected_task

    with patch.object(service.logger, "info") as mock_log:
        result = service.create_task(data)

    mock_repository.add_task.assert_called_once_with(data)
    mock_log.assert_any_call(f"Creating task for user: {data.user_name}")
    assert result == expected_task