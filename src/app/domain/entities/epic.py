from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

from src.app.domain.value_objects import IssueId, StoryPoints, Priority, LabelSet
from src.app.domain.exceptions import (
    BusinessRuleViolationException,
    InvalidStatusTransitionException,
)


class IssueType(str, Enum):
    EPIC = "epic"
    USER_STORY = "story"
    TASK = "task"
    BUG = "bug"


class IssueStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

    @classmethod
    def from_jira_status(cls, status: str) -> "IssueStatus":
        """Maps Jira status category to IssueStatus."""
        status_lower = status.lower()
        if (
            "done" in status_lower
            or "closed" in status_lower
            or "resolved" in status_lower
        ):
            return cls.DONE
        elif "progress" in status_lower or "review" in status_lower:
            return cls.IN_PROGRESS
        elif (
            "to do" in status_lower
            or "open" in status_lower
            or "backlog" in status_lower
        ):
            return cls.TODO
        raise InvalidStatusTransitionException(
            entity_key="",
            current_status=status,
            target_status=status,
            valid_transitions=[e.value for e in cls],
        )


@dataclass
class Epic:
    """
    Domain entity representing a Jira Epic.

    An Epic is a large body of work that can be broken down into smaller stories.
    Use the factory method `create()` to instantiate.
    """

    id: IssueId
    summary: str
    description: str
    status: IssueStatus
    created_at: datetime
    updated_at: datetime
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    priority: Optional[Priority] = None
    labels: LabelSet = field(default_factory=LabelSet.empty)
    story_points: Optional[StoryPoints] = None
    parent: Optional[IssueId] = None

    # Prevent direct instantiation
    def __init__(self, *args, **kwargs):
        raise TypeError("Use Epic.create() to instantiate Epic")

    @classmethod
    def create(
        cls,
        key: str,
        numeric_id: int,
        summary: str,
        description: str,
        status: IssueStatus,
        created_at: datetime,
        updated_at: datetime,
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_points: Optional[int] = None,
        parent_key: Optional[str] = None,
    ) -> "Epic":
        """
        Factory method to create an Epic instance.

        Args:
            key: Jira issue key (e.g., "PROJ-123")
            numeric_id: Jira numeric issue ID
            summary: Epic title/summary
            description: Epic description
            status: Current status
            created_at: Creation timestamp
            updated_at: Last update timestamp
            assignee: Assignee username (optional)
            reporter: Reporter username (optional)
            priority: Priority name from Jira (optional)
            labels: List of label names (optional)
            story_points: Story point estimate (optional)
            parent_key: Parent epic key if nested (optional)

        Returns:
            New Epic instance

        Raises:
            BusinessRuleViolationException: If required fields are missing or invalid
        """
        if not key:
            raise BusinessRuleViolationException(
                "Epic key is required", details="key cannot be empty"
            )
        if not summary or not summary.strip():
            raise BusinessRuleViolationException(
                "Epic summary is required", entity_key=key
            )
        if numeric_id < 0:
            raise BusinessRuleViolationException(
                "Numeric ID must be non-negative", entity_key=key
            )

        return cls._create(
            id=IssueId(key=key, numeric_id=numeric_id),
            summary=summary,
            description=description,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            assignee=assignee,
            reporter=reporter,
            priority=Priority.from_jira_name(priority) if priority else None,
            labels=LabelSet.from_list(labels) if labels else LabelSet.empty(),
            story_points=StoryPoints.from_optional(story_points),
            parent=IssueId.from_string(parent_key) if parent_key else None,
        )

    @classmethod
    def _create(
        cls,
        id: IssueId,
        summary: str,
        description: str,
        status: IssueStatus,
        created_at: datetime,
        updated_at: datetime,
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        priority: Optional[Priority] = None,
        labels: Optional[LabelSet] = None,
        story_points: Optional[StoryPoints] = None,
        parent: Optional[IssueId] = None,
    ) -> "Epic":
        """Internal factory for pre-constructed value objects."""
        instance = object.__new__(cls)
        instance.id = id
        instance.summary = summary
        instance.description = description
        instance.status = status
        instance.created_at = created_at
        instance.updated_at = updated_at
        instance.assignee = assignee
        instance.reporter = reporter
        instance.priority = priority
        instance.labels = labels if labels is not None else LabelSet.empty()
        instance.story_points = story_points
        instance.parent = parent
        return instance

    @property
    def key(self) -> str:
        return self.id.key

    @property
    def numeric_id(self) -> int:
        return self.id.numeric_id

    def is_completed(self) -> bool:
        return self.status == IssueStatus.DONE

    def __str__(self) -> str:
        return f"Epic({self.key}: {self.summary})"
