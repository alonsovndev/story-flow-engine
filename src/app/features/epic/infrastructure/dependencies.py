from src.app.features.epic.application.ports import EpicRepository
from src.app.features.epic.infrastructure.jira_epic_repository import (
    JiraEpicRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


def get_epic_repository() -> EpicRepository:
    """
    Composition-root factory: binds the epic port to its Jira HTTP adapter.
    """
    return JiraEpicRepository(JiraSettings.from_config())
