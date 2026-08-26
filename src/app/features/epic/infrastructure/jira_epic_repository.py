from typing import List, Optional

import httpx

from src.app.core.domain.exceptions import (
    BusinessRuleViolationException,
    UnauthorizedWorkspaceAccess,
)
from src.app.core.domain.issue import IssueStatus
from src.app.core.domain.value_objects import IssueId
from src.app.features.epic.application.ports import EpicRepository
from src.app.features.epic.domain import Epic
from src.app.infrastructure.external.jira.parsing import parse_jira_datetime
from src.app.infrastructure.external.jira.settings import JiraSettings
from src.app.shared.log_config import get_logger

logger = get_logger(__name__)


def map_epic(data: dict) -> Epic:
    """
    Map Jira API response data to the Epic domain entity.

    Args:
        data: Jira API response data.

    Returns:
        The mapped Epic entity.
    """
    fields = data["fields"]
    return Epic.create(
        key=data["key"],
        numeric_id=int(data["id"]),
        summary=fields.get("summary", ""),
        description=fields.get("description", ""),
        status=IssueStatus.from_jira_status(fields["status"]["name"]),
        created_at=parse_jira_datetime(fields["created"]),
        updated_at=parse_jira_datetime(fields["updated"]),
        reporter=fields.get("reporter", {}).get("displayName"),
        priority=fields.get("priority", {}).get("name")
        if fields.get("priority")
        else None,
        labels=fields.get("labels", []),
        story_points=fields.get("customfield_10011"),
    )


class JiraEpicRepository(EpicRepository):
    """Jira REST adapter for the EpicRepository port."""

    def __init__(self, settings: JiraSettings):
        self.settings = settings

    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        """
        Retrieve details of an epic by its key from Jira.

        Args:
            issue_id: The IssueId of the epic to retrieve.

        Returns:
            The Epic domain entity.

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.settings.base_url}/rest/api/3/issue/{issue_id.key}"
        # Never log credentials or full API bodies; they can contain PII.
        logger.info("Fetching epic from Jira", extra={"issue_key": issue_id.key})

        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.get(
                url,
                auth=(self.settings.email, self.settings.api_token),
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        data = response.json()

        return map_epic(data)

    async def create_epic(self, summary: str, description: str) -> Epic:
        """
        Create a new Epic in Jira.

        Args:
            summary: Summary of the epic.
            description: Description of the epic.

        Returns:
            The created Epic.

        Raises:
            BusinessRuleViolationException: If the creation fails due to
                invalid input or configuration.
        """
        url = f"{self.settings.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.settings.project_key},
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
            extra={"project_key": self.settings.project_key},
        )

        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(
                url,
                auth=(self.settings.email, self.settings.api_token),
                json=payload,
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

        return map_epic(data)

    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        if project_key != self.settings.project_key:
            raise UnauthorizedWorkspaceAccess(
                project_key, self.settings.project_key
            )
        return []
