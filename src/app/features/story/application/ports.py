from abc import ABC, abstractmethod
from typing import List, Optional

from src.app.core.domain.value_objects import IssueId
from src.app.features.story.domain import UserStory


class StoryRepository(ABC):
    """
    Port for persistence and retrieval of User Stories.

    Implemented by infrastructure adapters (e.g. the Jira REST client). The
    story feature depends only on this abstraction, never on a concrete client.
    """

    @abstractmethod
    async def get_user_story(self, issue_id: IssueId) -> Optional[UserStory]:
        """
        Retrieves a User Story by its IssueId.

        Args:
            issue_id: The identifier of the User Story.

        Returns:
            The UserStory entity, or None if not found.
        """
        pass

    @abstractmethod
    async def get_stories_in_epic(self, epic_id: IssueId) -> List[UserStory]:
        """
        Retrieves all User Stories belonging to a specific Epic.

        Args:
            epic_id: The identifier of the parent Epic.

        Returns:
            A list of UserStory entities.
        """
        pass

    @abstractmethod
    async def create_story(self, story: UserStory) -> UserStory:
        """
        Creates a new User Story.

        Args:
            story: The UserStory entity to create.

        Returns:
            The created UserStory entity, including the new ID from the source.
        """
        pass

    @abstractmethod
    async def update_story_status(self, issue_id: IssueId, new_status: str) -> None:
        """
        Updates the status of a User Story.

        Args:
            issue_id: The identifier of the User Story to update.
            new_status: The new status to set.
        """
        pass
