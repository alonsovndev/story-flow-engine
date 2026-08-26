import pytest

from src.app.core.domain.exceptions import UnauthorizedWorkspaceAccess
from src.app.features.epic.infrastructure.jira_epic_repository import (
    JiraEpicRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


@pytest.fixture
def jira_repository():
    """
    Test fixture to initialize JiraEpicRepository with a mocked configuration.
    """
    settings = JiraSettings.from_dict(
        {
            "base_url": "https://test-jira.atlassian.net",
            "email": "test@example.com",
            "api_token": "test_key",
            "project_key": "OPH",
        }
    )
    return JiraEpicRepository(settings)


@pytest.mark.asyncio
async def test_project_key_restrictions(jira_repository):
    """
    Ensure the repository prevents operations for unauthorized project keys.
    """
    # Arrange
    valid_project_key = "OPH"
    invalid_project_key = "INVALID"

    # Attempting to interact with an invalid project key should raise an exception
    with pytest.raises(UnauthorizedWorkspaceAccess):
        await jira_repository.find_epics_by_project(invalid_project_key)

    # Interacting with the valid project key should NOT raise any exceptions
    try:
        await jira_repository.find_epics_by_project(valid_project_key)
    except UnauthorizedWorkspaceAccess:
        pytest.fail("UnauthorizedWorkspaceAccess was raised for the valid project key.")
