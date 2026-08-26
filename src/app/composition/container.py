"""Composition root: wires ports to concrete infrastructure adapters.

The Container holds the assembled object graph for a single CLI invocation.
Presentation commands receive a Container instance rather than importing
feature-level factories, keeping the adapter choice fully behind the boundary.
"""

from dataclasses import dataclass

from src.app.features.epic.application.ports import EpicRepository
from src.app.features.epic.infrastructure.jira_epic_repository import (
    JiraEpicRepository,
)
from src.app.features.story.application.ports import StoryRepository
from src.app.features.story.infrastructure.jira_story_repository import (
    JiraStoryRepository,
)
from src.app.infrastructure.external.jira.settings import JiraSettings


@dataclass(frozen=True)
class Composition:
    """Immutable holder for all repository ports for one app lifecycle."""

    epic_repository: EpicRepository
    story_repository: StoryRepository


def build_composition(settings: JiraSettings) -> Composition:
    """Assemble the object graph from validated Jira settings.

    The caller owns loading and validating ``JiraSettings``. This function
    only performs the wiring — no config parsing, no singletons.
    """
    return Composition(
        epic_repository=JiraEpicRepository(settings),
        story_repository=JiraStoryRepository(settings),
    )
