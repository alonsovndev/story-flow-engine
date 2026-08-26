import os

import typer
from InquirerPy import inquirer

from src.app.composition.container import Composition, build_composition
from src.app.config.app_config import AppConfig
from src.app.features.epic.presentation.commands import create_epic, fetch_epic
from src.app.infrastructure.external.jira.settings import JiraSettings

# Initialize Typer app with help when no command is provided
app = typer.Typer(no_args_is_help=False)

_composition: Composition | None = None


def get_composition() -> Composition:
    """Lazily build the composition root on first access."""
    global _composition  # noqa: PLW0603
    if _composition is None:
        jira_config = AppConfig.instance().get_config("jira")
        settings = JiraSettings.from_dict(jira_config)
        _composition = build_composition(settings)
    return _composition


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


@app.command("fetch-epic")
def fetch_epic_command(
    issue_id: str = typer.Argument(..., help="Jira issue key, e.g. PROJ-123"),
):
    """Fetch an epic and its stories from Jira by key."""
    fetch_epic(get_composition(), issue_id)


@app.command("create-epic")
def create_epic_command(
    file_path: str = typer.Argument(..., help="Path to the epic markdown file"),
):
    """Create a new epic in Jira from a markdown file."""
    create_epic(get_composition(), file_path)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Story Flow Engine: turn Markdown epics and stories into Jira issues.

    Runs the interactive menu when no command is provided.
    """
    if ctx.invoked_subcommand is None:
        show_welcome_message()
        interactive_menu(skip_initial_prompt=False)


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
            fetch_epic(get_composition(), jira_key)
        elif menu_choice == "create_epic":
            file_path = inquirer.text(
                message="Enter the path to the Epic file:"
            ).execute()
            if not file_path:
                file_path = "data/EPIC-0-foundational/epic-0.md"

            create_epic(get_composition(), file_path)
        elif menu_choice == "exit":
            typer.echo("Thanks for using Story Flow Engine! Have a great day!")
            break


if __name__ == "__main__":
    app()
