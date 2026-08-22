from src.app.application.dtos.epic_dto import EpicDtoResponse
from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.application.mappers.epic_mapper import EpicDataMapper
from src.app.application.mappers.epic_markdown_parser import EpicMarkdownParser


class CreateEpicFromMarkdown:
    """
    Use case to create an Epic in Jira from the project's markdown format.

    Orchestrates parsing of the markdown document and delegation to the
    Jira repository, returning the created epic as a DTO.
    """

    def __init__(self, jira_repository: JiraRepository):
        """
        Initializes the use case with a Jira repository.

        Args:
            jira_repository: A concrete implementation of the JiraRepository interface.
        """
        self.jira_repository = jira_repository

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

        epic = await self.jira_repository.create_epic(
            summary=summary, description=description
        )

        return EpicDataMapper.to_epic_dto(epic, stories=[])
