from src.app.features.epic.application.dtos import EpicDtoResponse
from src.app.features.epic.application.mappers import EpicDataMapper
from src.app.features.epic.application.markdown_parser import EpicMarkdownParser
from src.app.features.epic.application.ports import EpicRepository


class CreateEpicFromMarkdown:
    """
    Use case to create an Epic in Jira from the project's markdown format.

    Orchestrates parsing of the markdown document and delegation to the
    Jira repository, returning the created epic as a DTO.
    """

    def __init__(self, epic_repository: EpicRepository):
        """
        Initializes the use case with an epic repository.

        Args:
            epic_repository: A concrete implementation of the EpicRepository port.
        """
        self.epic_repository = epic_repository

    async def execute(self, markdown_content: str) -> EpicDtoResponse:
        """
        Parses the markdown content and creates the Epic in Jira.

        Args:
            markdown_content: Full text of an Epic markdown document.

        Returns:
            An EpicDtoResponse for the newly created epic.

        Raises:
            BusinessRuleViolationException: If required fields are missing
                from the markdown or Jira rejects the creation.
        """
        summary, description = EpicMarkdownParser.parse(markdown_content)

        epic = await self.epic_repository.create_epic(
            summary=summary, description=description
        )

        return EpicDataMapper.to_epic_dto(epic, stories=[])
