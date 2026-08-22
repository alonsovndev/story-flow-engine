import typer
import asyncio
from src.app.application.use_cases.create_epic_from_markdown import (
    CreateEpicFromMarkdown,
)
from src.app.application.use_cases.get_epic_with_stories import GetEpicWithStories
from src.app.domain.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
)
from src.app.infrastructure.external.jira.dependencies import get_jira_repository
from InquirerPy import inquirer
import os

# Initialize Typer app with help when no command is provided
app = typer.Typer(no_args_is_help=False)


def show_welcome_message():
    """Display the welcome message."""
    typer.echo("╭──────────────────────────────────────────────────────────────╮")
    typer.echo("│   ███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗                │")
    typer.echo("│   ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝                │")
    typer.echo("│   ███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝                 │")
    typer.echo("│   ╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝                  │")
    typer.echo("│   ███████║   ██║   ╚██████╔╝██║  ██║   ██║                   │")
    typer.echo("│   ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝                   │")
    typer.echo("│                                                              │")
    typer.echo("│        🤖 Story Flow Engine                                  │")
    typer.echo("│        Intelligent Jira Automation Assistant                 │")
    typer.echo("╰──────────────────────────────────────────────────────────────╯")
    typer.echo("")
    typer.echo("System ready.")
    typer.echo("")


def interactive_menu(skip_initial_prompt=False):
    """Handles the interactive user menu."""
    while True:
        if not skip_initial_prompt:
            skip_initial_prompt = True
        else:
            typer.echo("\nPress Enter to go back to the main menu...")
            input()
        os.system("cls" if os.name == "nt" else "clear")
        show_welcome_message()
        menu_options = {
            "get_epic": "Retrieve an epic and its stories by JIRA key",
            "create_epic": "Create a new epic in JIRA from file",
            "exit": "Exit the application",
        }
        menu_choice = inquirer.select(
            message="Select an option:",
            choices=[
                {"name": description, "value": key}
                for key, description in menu_options.items()
            ],
        ).execute()

        if menu_choice == "get_epic":
            jira_key = inquirer.text(message="Enter the JIRA key:").execute()
            fetch_epic(jira_key)
        elif menu_choice == "create_epic":
            file_path = inquirer.text(
                message="Enter the path to the Epic file:"
            ).execute()
            if not file_path:
                file_path = "data/EPIC-0-foundational/epic-0.md"

            create_epic(file_path)
        elif menu_choice == "exit":
            typer.echo("Thanks for using Story Flow Engine! Have a great day!")
            break


def fetch_epic(issue_id: str):
    """
    Fetch an epic and its stories from JIRA using the epic key.

    Args:
        issue_id (str): The key of the epic to retrieve (e.g. "PROJ-123").
    """

    async def main():
        repository = get_jira_repository()
        use_case = GetEpicWithStories(jira_repository=repository)
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
        file_path (str): Path to the markdown file describing the epic.
    """

    async def main():
        repository = get_jira_repository()
        use_case = CreateEpicFromMarkdown(jira_repository=repository)

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


if __name__ == "__main__":
    show_welcome_message()
    interactive_menu(skip_initial_prompt=False)
