from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class StoryDtoResponse(BaseModel):
    """Data Transfer Object for User Stories."""

    key: str
    numeric_id: int
    summary: str
    description: str
    status: str
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    priority: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    story_points: Optional[int] = None
    epic_key: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    sprint: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EpicDtoResponse(BaseModel):
    """Data Transfer Object for Epics, including their stories."""

    key: str
    numeric_id: int
    summary: str
    description: str
    status: str
    assignee: Optional[str]
    reporter: Optional[str]
    priority: Optional[str]
    labels: List[str]
    story_points: Optional[int]
    created_at: datetime
    updated_at: datetime
    user_stories: List[StoryDtoResponse] = Field(default_factory=list)
