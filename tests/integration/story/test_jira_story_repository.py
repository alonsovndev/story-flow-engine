import pytest
import respx
from httpx import Response

from src.app.core.domain.issue import IssueStatus
from src.app.core.domain.value_objects import IssueId, Priority
from src.app.features.story.domain import UserStory
from src.app.features.story.infrastructure.jira_story_repository import (
    JiraStoryRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


@pytest.fixture
def story_repository():
    """Fixture to create a JiraStoryRepository instance for testing."""
    settings = JiraSettings.from_dict(
        {
            "base_url": "https://test-jira.atlassian.net",
            "email": "test@example.com",
            "api_token": "test_key",
            "project_key": "PROJ-1",
        }
    )
    return JiraStoryRepository(settings)


@pytest.mark.asyncio
@respx.mock
async def test_get_stories_in_epic_success(story_repository):
    """
    Test retrieval of all user stories belonging to an epic.
    """
    # Arrange
    epic_key = "PROJ-1"
    mock_response = {
        "issues": [
            {
                "id": "20001",
                "key": "PROJ-2",
                "fields": {
                    "summary": "First story",
                    "description": "Do things",
                    "status": {"name": "In Progress"},
                    "reporter": {"displayName": "Test User"},
                    "priority": {"name": "High"},
                    "labels": ["backend"],
                    "customfield_10011": 5,
                    "created": "2026-01-01T10:00:00.000-0500",
                    "updated": "2026-01-02T11:00:00.000-0500",
                },
            },
            {
                "id": "20002",
                "key": "PROJ-3",
                "fields": {
                    "summary": "Second story",
                    "description": "Do more things",
                    "status": {"name": "Done"},
                    "created": "2026-01-01T10:00:00.000-0500",
                    "updated": "2026-01-03T11:00:00.000-0500",
                },
            },
        ]
    }

    respx.post("https://test-jira.atlassian.net/rest/api/3/search").mock(
        return_value=Response(200, json=mock_response)
    )

    # Act
    stories = await story_repository.get_stories_in_epic(
        IssueId.from_string(epic_key)
    )

    # Assert
    assert [story.key for story in stories] == ["PROJ-2", "PROJ-3"]
    first = stories[0]
    assert isinstance(first, UserStory)
    assert first.summary == "First story"
    assert first.status == IssueStatus.IN_PROGRESS
    assert first.priority == Priority.high()
    assert first.story_points.value == 5
    assert first.epic_link is not None
    assert str(first.epic_link) == epic_key
    assert stories[1].priority is None


@pytest.mark.asyncio
@respx.mock
async def test_get_stories_in_epic_empty(story_repository):
    """
    Test that an epic without stories yields an empty list.
    """
    # Arrange
    respx.post("https://test-jira.atlassian.net/rest/api/3/search").mock(
        return_value=Response(200, json={"issues": []})
    )

    # Act
    stories = await story_repository.get_stories_in_epic(
        IssueId.from_string("PROJ-1")
    )

    # Assert
    assert stories == []
