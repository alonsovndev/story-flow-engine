from src.app.application.interfaces.jira_repository import JiraRepository
from src.app.config.app_config import AppConfig
from src.app.infrastructure.external.jira.jira_api_repository_impl import (
    JiraApiRepositoryImpl,
)


def get_jira_repository() -> JiraRepository:
    """
    Composition-root factory: binds the Jira port to its HTTP adapter.
    Configuration is handled via AppConfig.
    """
    config = AppConfig.instance()
    jira_config = config.get_config("jira")

    return JiraApiRepositoryImpl(jira_config)
