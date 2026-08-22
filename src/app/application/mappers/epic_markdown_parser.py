from src.app.domain.exceptions import BusinessRuleViolationException


class EpicMarkdownParser:
    """Parses the project's Epic markdown format into Jira-ready fields."""

    _KEY_PREFIX = "**Epic Key**:"
    _TITLE_PREFIX = "**Epic Title**:"
    _DESCRIPTION_PREFIX = "**Epic Description:**"

    @staticmethod
    def parse(markdown_content: str) -> tuple[str, str]:
        """
        Extracts ``(summary, description)`` from an Epic markdown document.

        Raises:
            BusinessRuleViolationException: If 'Epic Key' or 'Epic Title'
                is missing from the document.
        """
        lines = markdown_content.splitlines()

        epic_key = None
        epic_title = None
        description_lines: list[str] = []

        for idx, line in enumerate(lines):
            if line.startswith(EpicMarkdownParser._KEY_PREFIX):
                epic_key = line.split(":", 1)[1].strip()
            elif line.startswith(EpicMarkdownParser._TITLE_PREFIX):
                epic_title = line.split(":", 1)[1].strip()
            elif line.startswith(EpicMarkdownParser._DESCRIPTION_PREFIX):
                description_lines = lines[idx + 1 :]

        if not epic_key or not epic_title:
            raise BusinessRuleViolationException(
                "Epic markdown is missing required fields",
                details="'Epic Key' and 'Epic Title' are required",
            )

        summary = f"{epic_key} - {epic_title}"
        description = "\n".join(line.strip() for line in description_lines).strip()
        return summary, description
