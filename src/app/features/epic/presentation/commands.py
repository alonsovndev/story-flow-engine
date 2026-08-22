"""CLI command handlers for the epic feature.

These functions are the presentation-layer entry points for epic flows. They
are wired to the application use cases via the feature composition roots and
are reused by both the interactive menu and the direct Typer commands.
"""

import asyncio

import typer

from src.app.core.domain.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
)
from src.app.features.epic.application.use_cases import (
    CreateEpicFromMarkdown,
    GetEpicWithStories,
)
from src.app.features.epic.infrastructure.dependencies import get_epic_repository
from src.app.features.story.infrastructure.dependencies import get_story_repository


def fetch_epic(issue_id: str):
    """
    Fetch an epic and its stories from JIRA using the epic key.

    Args:
        issue_id: The key of the epic to retrieve (e.g. "PROJ-123").
    """

    async def main():
        use_case = GetEpicWithStories(
            epic_repository=get_epic_repository(),
            story_repository=get_story_repository(),
        )
        try:
            dto = await use_case.execute(issue_id)
            typer.echo("Epic Summary:")
            typer.echo(f"Key: {dto.key}")
            typer.echo(f"Summary: {dto.summary}")
            typer.echo(f"Description: {dto.description}")
            typer.echo("")
            typer.echo(f"Stories ({len(dto.user_stories)}):")
            for story in dto.user_stories:
                status = f" [{story.status}]" if story.status else ""
                typer.echo(f"  - {story.key}: {story.summary}{status}")
        except EntityNotFoundException:
            typer.echo(f"Epic not found: {issue_id}")
        except BusinessRuleViolationException as e:
            typer.echo(f"Error fetching epic: {e}")
        except Exception as e:  # keep interactive session alive on unexpected errors
            typer.echo(f"Unexpected error fetching epic: {e}")

    # Use asyncio.run to handle the async call
    asyncio.run(main())


def create_epic(file_path: str):
    """
    Create a new epic in JIRA from an Epic markdown file.

    Args:
        file_path: Path to the markdown file describing the epic.
    """

    async def main():
        use_case = CreateEpicFromMarkdown(epic_repository=get_epic_repository())

        try:
            with open(file_path, "r") as file:
                markdown_content = file.read()
        except OSError as e:
            # OSError covers missing, unreadable, and directory paths.
            typer.echo(f"Cannot read file. Error: {e}")
            return

        try:
            dto = await use_case.execute(markdown_content)
        except BusinessRuleViolationException as e:
            typer.echo(f"Invalid file or content. Error: {e}")
            return

        typer.echo("Epic Successfully Created!")
        typer.echo(f"Key: {dto.key}")
        typer.echo(f"Summary: {dto.summary}")
        typer.echo(f"Description: {dto.description}")

    # Use asyncio.run to handle the async call
    asyncio.run(main())
