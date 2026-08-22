import pytest
import respx
from datetime import datetime
from httpx import Response

from src.app.core.domain.exceptions import BusinessRuleViolationException
from src.app.core.domain.value_objects import IssueId, Priority
from src.app.features.epic.domain import Epic
from src.app.features.epic.infrastructure.jira_epic_repository import (
    JiraEpicRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


@pytest.fixture
def epic_repository():
    """
    Fixture to create a JiraEpicRepository instance for testing.
    """
    settings = JiraSettings.from_dict(
        {
            "base_url": "https://test-jira.atlassian.net",
            "email": "test@example.com",
            "api_token": "test_key",
            "project_key": "PROJ-1",
        }
    )
    return JiraEpicRepository(settings)


@pytest.mark.asyncio
@respx.mock
async def test_get_epic_success(epic_repository):
    """
    Test successful retrieval of an Epic from the Jira API.
    """
    # Arrange
    epic_key = "PROJ-1"
    mock_response = {
        "id": "10001",
        "key": epic_key,
        "fields": {
            "summary": "Test Epic from API",
            "description": "A detailed description.",
            "status": {"name": "To Do"},
            "creator": {"displayName": "Test User"},
            "reporter": {"displayName": "Test User"},
            "priority": {"name": "High"},
            "labels": ["backend", "api"],
            "customfield_10011": 8.0,  # Story Points
            "created": "2025-01-01T10:00:00.000-0500",
            "updated": "2025-01-02T11:00:00.000-0500",
        },
    }

    respx.get(f"https://test-jira.atlassian.net/rest/api/3/issue/{epic_key}").mock(
        return_value=Response(200, json=mock_response)
    )

    # Act
    epic = await epic_repository.get_epic(IssueId.from_string(epic_key))

    # Assert
    assert epic is not None
    assert isinstance(epic, Epic)
    assert epic.key == epic_key
    assert epic.summary == "Test Epic from API"
    assert epic.story_points.value == 8
    assert len(epic.labels) == 2
    assert epic.labels.has_label_named("backend")


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_success(epic_repository):
    """
    Test successful creation of an Epic in the Jira API.
    """
    # Arrange
    epic_key = "PROJ-100"

    mock_response = {
        "id": "10001",
        "key": epic_key,
        "fields": {
            "summary": "Test Epic Creation",
            "description": "A test epic for unit testing integration with Jira.",
            "priority": {"name": "High"},
            "status": {"name": "To Do"},
            "created": "2026-01-01T10:00:00.000-0500",
            "updated": "2026-01-01T11:00:00.000-0500",
        },
    }

    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(201, json=mock_response)
    )

    # Act
    epic = await epic_repository.create_epic(
        summary="Test Epic Creation",
        description="A test epic for unit testing integration with Jira.",
    )

    # Assert
    assert epic is not None
    assert isinstance(epic, Epic)
    assert epic.key == epic_key
    assert epic.summary == "Test Epic Creation"
    assert epic.description == "A test epic for unit testing integration with Jira."
    assert epic.priority == Priority.high()
    assert epic.created_at == datetime.fromisoformat("2026-01-01T10:00:00-05:00")
    assert epic.updated_at == datetime.fromisoformat("2026-01-01T11:00:00-05:00")


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_unauthorized(epic_repository):
    """
    Test Epic creation fails with 401 Unauthorized.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(
            401, json={"errorMessages": ["Unauthorized"], "errors": {}}
        )
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await epic_repository.create_epic(
            summary="Unauthorized Epic",
            description="Testing unauthorized response handling.",
        )

    assert "Unauthorized" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_internal_server_error(epic_repository):
    """
    Test Epic creation fails with 500 Internal Server Error.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(
            500, json={"errorMessages": ["Internal Server Error"], "errors": {}}
        )
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await epic_repository.create_epic(
            summary="Epic causing 500",
            description="Testing internal server error handling.",
        )

    assert "Internal Server Error" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_create_epic_invalid_payload(epic_repository):
    """
    Test Epic creation fails with 400 Bad Request due to invalid payload.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/issue").mock(
        return_value=Response(
            400,
            json={
                "errorMessages": ["Invalid payload"],
                "errors": {"summary": "Summary is required"},
            },
        )
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await epic_repository.create_epic(
            summary="",  # Invalid because the summary is empty
            description="Epic with invalid payload.",
        )

    assert "Invalid payload" in str(exc_info.value)
    assert "Summary is required" in str(exc_info.value)
