import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.app.core.domain.exceptions import EntityNotFoundException
from src.app.core.domain.issue import IssueStatus
from src.app.features.epic.application.use_cases import GetEpicWithStories
from src.app.features.epic.domain import Epic
from src.app.features.story.domain import UserStory


@pytest.fixture
def mock_epic_repo():
    """Fixture to create a mock EpicRepository."""
    return AsyncMock()


@pytest.fixture
def mock_story_repo():
    """Fixture to create a mock StoryRepository."""
    return AsyncMock()


@pytest.mark.asyncio
class TestGetEpicWithStories:
    async def test_get_epic_and_stories_successfully(
        self, mock_epic_repo, mock_story_repo
    ):
        # Arrange
        epic_key = "PROJ-1"
        story_key = "PROJ-2"

        # Create mock domain entities
        mock_epic = Epic.create(
            key=epic_key,
            numeric_id=1,
            summary="Test Epic",
            description="Desc",
            status=IssueStatus.TODO,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_story = UserStory.create(
            key=story_key,
            numeric_id=2,
            summary="Test Story",
            description="Desc",
            status=IssueStatus.TODO,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            epic_key=epic_key,
        )

        mock_epic_repo.get_epic.return_value = mock_epic
        mock_story_repo.get_stories_in_epic.return_value = [mock_story]

        use_case = GetEpicWithStories(
            epic_repository=mock_epic_repo, story_repository=mock_story_repo
        )

        # Act
        result = await use_case.execute(epic_key)

        # Assert
        assert result.key == epic_key
        assert result.summary == "Test Epic"
        assert len(result.user_stories) == 1
        assert result.user_stories[0].key == story_key

        mock_epic_repo.get_epic.assert_called_once()
        mock_story_repo.get_stories_in_epic.assert_called_once_with(mock_epic.id)

    async def test_epic_not_found_raises_exception(self, mock_epic_repo, mock_story_repo):
        # Arrange
        epic_key = "PROJ-999999"
        mock_epic_repo.get_epic.return_value = None

        use_case = GetEpicWithStories(
            epic_repository=mock_epic_repo, story_repository=mock_story_repo
        )

        # Act & Assert
        with pytest.raises(EntityNotFoundException) as exc_info:
            await use_case.execute(epic_key)

        assert "Epic not found" in str(exc_info.value)
        assert epic_key in str(exc_info.value)
        mock_epic_repo.get_epic.assert_called_once()
        mock_story_repo.get_stories_in_epic.assert_not_called()

    async def test_epic_with_no_stories(self, mock_epic_repo, mock_story_repo):
        # Arrange
        epic_key = "PROJ-3"
        mock_epic = Epic.create(
            key=epic_key,
            numeric_id=3,
            summary="Epic with no stories",
            description="Desc",
            status=IssueStatus.TODO,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_epic_repo.get_epic.return_value = mock_epic
        mock_story_repo.get_stories_in_epic.return_value = []

        use_case = GetEpicWithStories(
            epic_repository=mock_epic_repo, story_repository=mock_story_repo
        )

        # Act
        result = await use_case.execute(epic_key)

        # Assert
        assert result.key == epic_key
        assert len(result.user_stories) == 0
        mock_story_repo.get_stories_in_epic.assert_called_once_with(mock_epic.id)
