from typing import List, Optional

import httpx

from src.app.core.domain.issue import IssueStatus
from src.app.core.domain.value_objects import IssueId
from src.app.features.story.application.ports import StoryRepository
from src.app.features.story.domain import UserStory
from src.app.infrastructure.external.jira.parsing import parse_jira_datetime
from src.app.infrastructure.external.jira.settings import JiraSettings
from src.app.shared.log_config import get_logger

logger = get_logger(__name__)


def map_user_story(data: dict, epic_key: Optional[str] = None) -> UserStory:
    """
    Map a Jira API issue response to the UserStory domain entity.

    Args:
        data: Jira API issue data.
        epic_key: Parent epic key when known from the query context.

    Returns:
        The mapped UserStory entity.
    """
    fields = data["fields"]
    return UserStory.create(
        key=data["key"],
        numeric_id=int(data["id"]),
        summary=fields.get("summary", ""),
        description=fields.get("description", ""),
        status=IssueStatus.from_jira_status(fields["status"]["name"]),
        created_at=parse_jira_datetime(fields["created"]),
        updated_at=parse_jira_datetime(fields["updated"]),
        reporter=fields.get("reporter", {}).get("displayName"),
        priority=fields["priority"]["name"] if fields.get("priority") else None,
        labels=fields.get("labels", []),
        story_points=fields.get("customfield_10011"),
        epic_key=epic_key,
    )


class JiraStoryRepository(StoryRepository):
    """Jira REST adapter for the StoryRepository port."""

    def __init__(self, settings: JiraSettings):
        self.settings = settings

    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        raise NotImplementedError("get_user_story is not implemented yet")

    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        """
        Retrieve all user stories whose parent is the given epic.

        Args:
            epic_id: The IssueId of the parent epic.

        Returns:
            List of UserStory entities (empty when the epic has no stories).

        Raises:
            httpx.HTTPError: If the API request fails.
        """
        url = f"{self.settings.base_url}/rest/api/3/search"
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

        async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
            response = await client.post(
                url,
                auth=(self.settings.email, self.settings.api_token),
                json=payload,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        issues = response.json().get("issues", [])

        stories = [
            map_user_story(issue, epic_key=epic_id.key) for issue in issues
        ]
        logger.info(
            "Fetched stories for epic",
            extra={"issue_key": epic_id.key, "count": len(stories)},
        )
        return stories

    async def create_story(self, story: UserStory) -> UserStory:
        raise NotImplementedError("create_story is not implemented yet")

    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        raise NotImplementedError("update_story_status is not implemented yet")
