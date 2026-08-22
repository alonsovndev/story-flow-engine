from typing import List, Optional

import httpx
from src.app.infrastructure.external.jira.helpers import JiraApiHelpers

from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.domain import UserStory
from src.app.domain.exceptions import (
    UnauthorizedWorkspaceAccess,
    BusinessRuleViolationException,
)
from src.app.shared.log_config import get_logger
from src.app.domain.entities import Epic
from src.app.domain.value_objects import IssueId

logger = get_logger(__name__)


class JiraApiRepositoryImpl(JiraRepository):
    def __init__(self, jira_config: dict):
        """
        Initialize the JiraApiRepository with configuration from AppConfig.

        Args:
            jira_config (dict): A dictionary containing Jira configuration parameters such as:
                - base_url: The base URL of the Jira instance.
                - email: The email address of the Jira instance.
                - api_token: The API token of the Jira instance.
                - project_space_key: The project space key of the Jira instance.

        Raises:
            BusinessRuleViolationException: If required configuration entries are missing.
        """
        missing = [
            key
            for key in ("base_url", "email", "api_token", "project_key")
            if not jira_config.get(key)
        ]
        if missing:
            raise BusinessRuleViolationException(
                "Jira configuration is incomplete",
                details=f"missing: {', '.join(missing)}",
            )

        self.base_url: str = jira_config["base_url"]
        self.email: str = jira_config["email"]
        self.api_token: str = jira_config["api_token"]
        self.project_space_key: str = jira_config["project_key"]
        self.timeout = float(jira_config.get("timeout", 30))

    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        """
        Retrieve details of an epic by its key from Jira.

        Args:
            issue_id (IssueId): The IssueId of the epic to retrieve.

        Returns:
            Epic: The Epic domain entity.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_id.key}"
        # Never log credentials or full API bodies; they can contain PII.
        logger.info("Fetching epic from Jira", extra={"issue_key": issue_id.key})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                auth=(self.email, self.api_token),
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        data = response.json()

        return JiraApiHelpers.map_epic(data)

    async def create_epic(self, summary: str, description: str) -> Epic:
        """
        Create a new Epic in Jira.

        Args:
            summary (str): Summary of the epic.
            description (str): Description of the epic.

        Returns:
            Epic: The created Epic.

        Raises:
            BusinessRuleViolationException: If the creation fails due to invalid input or configuration.
        """
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_space_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description.strip()}],
                        }
                    ],
                },
                "issuetype": {"name": "Epic"},
            }
        }

        logger.info(
            "Creating a new Epic in Jira",
            extra={"project_key": self.project_space_key},
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, auth=(self.email, self.api_token), json=payload
            )

        if response.status_code != 201:
            # Jira error bodies are not guaranteed to be valid JSON.
            try:
                error_body = response.json()
            except ValueError:
                error_body = {}
            error_message = error_body.get("errorMessages", ["Unknown error"])
            logger.error(
                "Failed to create Epic in Jira",
                extra={"status_code": response.status_code},
            )
            raise BusinessRuleViolationException(
                f"Failed to create an Epic: {error_message}",
                details=error_body.get("errors", {}),
            )

        data = response.json()
        logger.info(
            "Epic successfully created in Jira",
            extra={"issue_key": data.get("key")},
        )

        return JiraApiHelpers.map_epic(data)

    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        raise NotImplementedError("get_user_story is not implemented yet")

    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        """
        Retrieve all user stories whose parent is the given epic.

        Args:
            epic_id (IssueId): The IssueId of the parent epic.

        Returns:
            List of UserStory entities (empty when the epic has no stories).

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.base_url}/rest/api/3/search"
        # POST is used because GET /search is deprecated on Jira Cloud v3.
        # 'parent = KEY' JQL matches stories under an epic for both
        # company-managed and team-managed projects.
        payload = {
            "jql": f"parent = {epic_id.key}",
            "maxResults": 100,
            "fields": [
                "summary",
                "description",
                "status",
                "created",
                "updated",
                "reporter",
                "priority",
                "labels",
                "customfield_10011",
            ],
        }
        logger.info("Fetching stories for epic", extra={"issue_key": epic_id.key})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                auth=(self.email, self.api_token),
                json=payload,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        issues = response.json().get("issues", [])

        stories = [
            JiraApiHelpers.map_user_story(issue, epic_key=epic_id.key)
            for issue in issues
        ]
        logger.info(
            "Fetched stories for epic",
            extra={"issue_key": epic_id.key, "count": len(stories)},
        )
        return stories

    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        if project_key != self.project_space_key:
            raise UnauthorizedWorkspaceAccess(project_key, self.project_space_key)
        return []

    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        raise NotImplementedError("update_story_status is not implemented yet")

    async def create_story(self, story: UserStory) -> UserStory:
        raise NotImplementedError("create_story is not implemented yet")
