from abc import ABC, abstractmethod
from typing import List, Optional

from src.app.core.domain.value_objects import IssueId
from src.app.features.epic.domain import Epic


class EpicRepository(ABC):
    """
    Port for persistence and retrieval of Epics.

    Implemented by infrastructure adapters (e.g. the Jira REST client). The
    epic feature depends only on this abstraction, never on a concrete client.
    """

    @abstractmethod
    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        """
        Retrieves an Epic by its IssueId.

        Args:
            issue_id: The identifier of the Epic.

        Returns:
            The Epic entity, or None if not found.
        """
        pass

    @abstractmethod
    async def create_epic(self, summary: str, description: str) -> Epic:
        """
        Creates a new Epic.

        Args:
            summary: The epic summary/title.
            description: The epic description.

        Returns:
            The created Epic entity, including the new ID from the source.
        """
        pass

    @abstractmethod
    async def find_epics_by_project(self, project_key: str) -> List[Epic]:
        """
        Finds all Epics within a given project.

        Args:
            project_key: The Jira project key.

        Returns:
            A list of Epic entities.
        """
        pass
