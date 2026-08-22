from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.domain.value_objects import IssueId
from src.app.domain.exceptions import EntityNotFoundException
from src.app.application.dtos.epic_dto import EpicDtoResponse
from src.app.application.mappers.epic_mapper import EpicDataMapper


class GetEpicWithStories:
    """
    Use case to retrieve an Epic and all its associated User Stories.

    This use case orchestrates the domain logic of fetching an epic,
    its child stories, and mapping them to a data transfer object (DTO).
    """

    def __init__(self, jira_repository: JiraRepository):
        """
        Initializes the use case with a Jira repository.

        Args:
            jira_repository: A concrete implementation of the JiraRepository interface.
        """
        self.jira_repository = jira_repository

    async def execute(self, epic_key: str) -> EpicDtoResponse:
        """
        Executes the use case.

        Args:
            epic_key: The key of the epic to retrieve (e.g., "PROJ-123").

        Returns:
            An EpicDtoResponse containing the epic and its user stories.

        Raises:
            EntityNotFoundException: If the epic with the given key does not exist.
        """
        epic_id = IssueId.from_string(epic_key)

        # 1. Fetch the Epic from the repository
        epic = await self.jira_repository.get_epic(epic_id)

        if not epic:
            raise EntityNotFoundException("Epic", epic_key)

        # 2. Fetch all User Stories linked to the Epic
        stories = await self.jira_repository.get_stories_in_epic(epic.id)

        # 3. Map entities to DTO
        return EpicDataMapper.to_epic_dto(epic, stories)
