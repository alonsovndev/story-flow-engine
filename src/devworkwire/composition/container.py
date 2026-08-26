"""Composition root: wires ports to concrete infrastructure adapters.

The Container holds the assembled object graph for a single CLI invocation.
Presentation commands receive a Container instance rather than importing
feature-level factories, keeping the adapter choice fully behind the boundary.
"""

from dataclasses import dataclass

from devworkwire.application.ports import WorkItemProvider
from devworkwire.config.project_config import ProjectConfig
from devworkwire.core.domain.exceptions import BusinessRuleViolationException
from devworkwire.infrastructure.external.jira.settings import JiraSettings
from devworkwire.infrastructure.external.jira.work_item_provider import (
    JiraWorkItemProvider,
)


@dataclass(frozen=True)
class Composition:
    """Immutable holder for the provider port for one app lifecycle."""

    work_item_provider: WorkItemProvider


def build_composition(
    settings: JiraSettings, project_config: ProjectConfig
) -> Composition:
    """Assemble the object graph from validated settings and project config.

    The caller owns loading and validating ``JiraSettings`` and
    ``ProjectConfig``. This function only performs the wiring — no config
    parsing, no singletons.

    Raises:
        BusinessRuleViolationException: If the configured provider has no
            adapter implementation.
    """
    if project_config.provider == "jira":
        provider: WorkItemProvider = JiraWorkItemProvider(settings, project_config)
    else:
        raise BusinessRuleViolationException(
            f"Unsupported provider: {project_config.provider}",
            details="No adapter is registered for this provider.",
        )
    return Composition(work_item_provider=provider)
