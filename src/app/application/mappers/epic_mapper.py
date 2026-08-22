from src.app.domain.entities import Epic, UserStory
from src.app.application.dtos import EpicDtoResponse, StoryDtoResponse


class EpicDataMapper:
    """Maps domain entities to DTOs."""

    @staticmethod
    def to_user_story_dto(story: UserStory) -> StoryDtoResponse:
        return StoryDtoResponse(
            key=story.key,
            numeric_id=story.numeric_id,
            summary=story.summary,
            description=story.description,
            status=story.status.value,
            assignee=story.assignee,
            reporter=story.reporter,
            priority=story.priority.name if story.priority else None,
            labels=[label.name for label in story.labels],
            story_points=story.story_points.value if story.story_points else None,
            epic_key=story.epic_link.key if story.epic_link else None,
            acceptance_criteria=story.acceptance_criteria,
            sprint=story.sprint,
            created_at=story.created_at,
            updated_at=story.updated_at,
        )

    @staticmethod
    def to_epic_dto(epic: Epic, stories: list[UserStory]) -> EpicDtoResponse:
        return EpicDtoResponse(
            key=epic.key,
            numeric_id=epic.numeric_id,
            summary=epic.summary,
            description=epic.description,
            status=epic.status.value,
            assignee=epic.assignee,
            reporter=epic.reporter,
            priority=epic.priority.name if epic.priority else None,
            labels=[label.name for label in epic.labels],
            story_points=epic.story_points.value if epic.story_points else None,
            created_at=epic.created_at,
            updated_at=epic.updated_at,
            user_stories=[EpicDataMapper.to_user_story_dto(story) for story in stories],
        )
