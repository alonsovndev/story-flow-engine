from src.app.core.domain.exceptions import EntityNotFoundException
from src.app.core.domain.value_objects import IssueId
from src.app.features.epic.application.dtos import EpicDtoResponse
from src.app.features.epic.application.mappers import EpicDataMapper
from src.app.features.epic.application.ports import EpicRepository
from src.app.features.story.application.ports import StoryRepository


class GetEpicWithStories:
    """
    Use case to retrieve an Epic and all its associated User Stories.

    This use case orchestrates fetching an epic and its child stories and
    mapping them to a data transfer object (DTO). It composes the epic
    feature's repository with the story feature's repository, reflecting that
    an epic aggregate is read together with its stories.
    """

    def __init__(
        self, epic_repository: EpicRepository, story_repository: StoryRepository
    ):
        """
        Initializes the use case with epic and story repositories.

        Args:
            epic_repository: A concrete implementation of the EpicRepository port.
            story_repository: A concrete implementation of the StoryRepository port.
        """
        self.epic_repository = epic_repository
        self.story_repository = story_repository

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
        epic = await self.epic_repository.get_epic(epic_id)

        if not epic:
            raise EntityNotFoundException("Epic", epic_key)

        # 2. Fetch all User Stories linked to the Epic
        stories = await self.story_repository.get_stories_in_epic(epic.id)

        # 3. Map entities to DTO
        return EpicDataMapper.to_epic_dto(epic, stories)
