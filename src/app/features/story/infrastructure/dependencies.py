from src.app.features.story.application.ports import StoryRepository
from src.app.features.story.infrastructure.jira_story_repository import (
    JiraStoryRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


def get_story_repository() -> StoryRepository:
    """
    Composition-root factory: binds the story port to its Jira HTTP adapter.
    """
    return JiraStoryRepository(JiraSettings.from_config())
