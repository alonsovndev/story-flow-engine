# Architecture Overview

Story Flow Engine follows **Clean Architecture** principles combined with **Domain-Driven Design** (DDD) patterns, organized as **vertical feature slices**. The goal is to keep domain logic independent of external concerns (Jira API, CLI framework, logging), making the system testable, maintainable, and adaptable to change.

## Feature Slices

Instead of one global layer stack, each business capability owns its full vertical slice under `src/app/features/`:

```
src/app/
├── config/                      # AppConfig singleton + environment YAML files
├── core/domain/                 # Shared kernel (issue types/statuses, value objects, exceptions)
├── features/
│   ├── epic/                    # Epic slice
│   │   ├── application/         # Use cases, ports, DTOs, mappers, markdown parsing
│   │   ├── domain/              # Epic entity
│   │   └── infrastructure/      # JiraEpicRepository + composition root
│   └── story/                   # Story slice
│       ├── application/         # Ports, DTOs, mappers
│       ├── domain/              # UserStory entity
│       └── infrastructure/      # JiraStoryRepository + composition root
├── infrastructure/external/jira/  # Shared Jira support (settings, datetime parsing)
├── presentation/                # CLI shell (Typer commands + interactive menu)
└── shared/                      # Cross-cutting utilities (logging, retry)
```

**Dependency rules:**

1. Features depend on `core` and `shared` — never the other way around.
2. Features never import each other's internals; the only allowed cross-feature dependency is **epic → story** (via story's port and DTOs/mappers).
3. Dependencies point inward inside each slice: `domain` knows nothing about `application`, which knows nothing about `infrastructure`.

```mermaid
graph TD
    subgraph "Presentation"
        CLI[CLI Shell - Typer + InquirerPy]
        CMD[Epic Commands]
    end

    subgraph "Feature: epic"
        EUC[Use Cases]
        EPORT[EpicRepository Port]
        EDOM[Epic Entity]
    end

    subgraph "Feature: story"
        SPORT[StoryRepository Port]
        SDTO[Story DTOs + Mapper]
        SDOM[UserStory Entity]
    end

    subgraph "Core Kernel"
        ISSUE[IssueType / IssueStatus]
        VO[Value Objects]
        EXC[Domain Exceptions]
    end

    subgraph "Infrastructure"
        EIMPL[JiraEpicRepository]
        SIMPL[JiraStoryRepository]
        SETTINGS[JiraSettings]
    end

    CLI --> CMD
    CMD --> EUC
    EUC --> EPORT
    EUC --> EDOM
    EPORT -.-> EIMPL
    EDOM --> ISSUE
    EDOM --> VO
    EDOM --> EXC
    SDOM --> ISSUE
    SDOM --> VO
    EUC --> SDTO
    EIMPL --> SETTINGS
    SIMPL --> SETTINGS
    EIMPL --> EDOM
    SIMPL --> SDOM

    style Core Kernel fill:#e1f5fe,stroke:#0288d1
    style Feature: epic fill:#fff3e0,stroke:#f57c00
    style Feature: story fill:#f3e5f5,stroke:#7b1fa2
    style Presentation fill:#fce4ec,stroke:#c62828
    style Infrastructure fill:#e8f5e9,stroke:#388e3c
```

## Request Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Shell (Presentation)
    participant UC as GetEpicWithStories (epic/application)
    participant ERepo as EpicRepository (Port)
    participant SRepo as StoryRepository (Port)
    participant EImpl as JiraEpicRepository (Infra)
    participant SImpl as JiraStoryRepository (Infra)
    participant Jira as Jira REST API

    User->>CLI: fetch-epic PROJ-123
    CLI->>UC: execute(epic_key)
    UC->>UC: IssueId.from_string(epic_key)
    UC->>ERepo: get_epic(issue_id)
    ERepo->>EImpl: get_epic(issue_id)
    EImpl->>Jira: GET /rest/api/3/issue/{key}
    Jira-->>EImpl: JSON response
    EImpl->>EImpl: map_epic(data)
    EImpl-->>UC: Epic entity
    UC->>SRepo: get_stories_in_epic(epic.id)
    SRepo->>SImpl: get_stories_in_epic(epic_id)
    SImpl->>Jira: POST /rest/api/3/search (JQL)
    Jira-->>SImpl: JSON response
    SImpl-->>UC: List[UserStory]
    UC->>UC: EpicDataMapper.to_epic_dto(epic, stories)
    UC-->>CLI: EpicDtoResponse
    CLI-->>User: Display epic details
```

## Core Kernel (`src/app/core/domain/`)

Concepts shared by every feature. Completely framework-agnostic.

#### Issue Abstractions (`issue.py`)

`IssueType` and `IssueStatus` describe what an issue *is* and where it *stands* — shared by epics and stories alike.

#### Value Objects (`value_objects/`)

Immutable, self-validating objects with no identity. Equality is based on value, not reference.

| Value Object | Description | Key Behavior |
|-------------|-------------|--------------|
| `IssueId` | Jira issue key + numeric ID | Parsed from strings like `PROJ-123` |
| `Priority` | Priority level (Highest → Lowest) | Comparison: `priority.is_higher_than(other)` |
| `StoryPoints` | Estimation points | Arithmetic: `sp1 + sp2`, `sp * 3` |
| `Label` | Case-insensitive tag | Max 255 chars, non-empty validation |
| `LabelSet` | Immutable collection of labels | Set operations: `add()`, `remove()`, `contains()` |

All value objects use `@dataclass(frozen=True)` for immutability.

#### Domain Exceptions (`exceptions/`)

Structured error hierarchy rooted at `DomainException`:

```
DomainException
├── EntityNotFoundException      # Epic/story not found
├── BusinessRuleViolationException  # Invalid data or state
├── DuplicateEntityException     # Duplicate issue detected
├── InvalidStatusTransitionException  # Illegal status change
└── UnauthorizedWorkspaceAccess  # Cross-project access attempt
```

## Epic Feature (`src/app/features/epic/`)

Everything the epic capability needs, in one place.

### Domain (`domain/epic.py`)

**`Epic`** — A large body of work that can contain multiple stories. Uses the **Factory Method** pattern — direct `__init__` is blocked; use `.create()`:

```python
epic = Epic.create(
    key="PROJ-123",
    numeric_id=10042,
    summary="User Authentication System",
    description="Implement OAuth2-based authentication...",
    status=IssueStatus.TODO,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    priority="High",
    labels=["auth", "security"],
    story_points=21,
)
```

Invariants are enforced at construction time: keys can't be empty, numeric IDs must be non-negative, summaries are required.

### Application (`application/`)

Orchestrates domain objects to fulfill use cases. Depends only on abstractions.

#### Use Cases

Each use case is a single-responsibility class receiving its dependencies via constructor injection:

```python
class GetEpicWithStories:
    def __init__(self, epic_repository: EpicRepository, story_repository: StoryRepository):
        self.epic_repository = epic_repository
        self.story_repository = story_repository

    async def execute(self, epic_key: str) -> EpicDtoResponse:
        epic_id = IssueId.from_string(epic_key)
        epic = await self.epic_repository.get_epic(epic_id)
        if not epic:
            raise EntityNotFoundException("Epic", epic_key)
        stories = await self.story_repository.get_stories_in_epic(epic.id)
        return EpicDataMapper.to_epic_dto(epic, stories)
```

Note how the epic use case consumes the **story port** — cross-feature collaboration happens through interfaces, never through imports of story internals beyond its public API (`ports.py`, `dtos.py`, `mappers.py`).

#### Repository Ports (`ports.py`)

Abstract base classes defining the contracts for epic operations:

```python
class EpicRepository(ABC):
    @abstractmethod
    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]: ...
    @abstractmethod
    async def create_epic(self, summary: str, description: str) -> Epic: ...
    @abstractmethod
    async def find_epics_by_project(self, project_key: str) -> List[Epic]: ...
```

Ports allow swapping implementations (mock for tests, different API client) without touching business logic.

#### DTOs and Mappers

DTOs define the data shape at boundaries; mappers transform between them:

```
Epic entity → EpicDataMapper.to_epic_dto() → EpicDtoResponse
```

`EpicDtoResponse` embeds `StoryDtoResponse` items owned by the story feature.

#### Markdown Parsing (`markdown_parser.py`)

`EpicMarkdownParser` extracts epic title/key/description from Markdown source files — an application concern feeding `CreateEpicFromMarkdown`.

### Infrastructure (`infrastructure/jira_epic_repository.py`)

Concrete implementation of `EpicRepository` using `httpx` for async HTTP calls:

```python
class JiraEpicRepository(EpicRepository):
    def __init__(self, settings: JiraSettings):
        self.settings = settings

    async def get_epic(self, issue_id: IssueId) -> Optional[Epic]:
        url = f"{self.settings.base_url}/rest/api/3/issue/{issue_id.key}"
        ...
        return map_epic(response.json())
```

Module-level mapper functions (`map_epic`) convert raw JSON into domain entities via factory methods. `dependencies.py` is the composition root:

```python
def get_epic_repository() -> JiraEpicRepository:
    return JiraEpicRepository(JiraSettings.from_config())
```

## Story Feature (`src/app/features/story/`)

Mirrors the epic layout at smaller scope:

- **Domain**: `UserStory` entity with `create(key=..., epic_key=...)` factory.
- **Application**: `StoryRepository` port, `StoryDtoResponse`/`CreateStoryDtoRequest` DTOs, `StoryDataMapper`.
- **Infrastructure**: `JiraStoryRepository` implementing `get_stories_in_epic` (JQL search for children of an epic); remaining operations raise `NotImplementedError` until needed.

The story feature has **no knowledge of the epic feature** — it exposes a port and DTOs that epic consumes.

## Shared Infrastructure Support (`src/app/infrastructure/external/jira/`)

Cross-feature plumbing used by both adapters:

- **`settings.py`** — `JiraSettings`: frozen dataclass holding `base_url`, `email`, `api_token`, `project_key`, `timeout`. Built via `from_dict()` (validates required keys, raising `BusinessRuleViolationException` when incomplete) or `from_config()` (reads the `jira` block from `AppConfig`).
- **`parsing.py`** — `parse_jira_datetime()` converts Jira's timestamp format into timezone-aware datetimes.

## Configuration (`src/app/config/`)

Thread-safe `AppConfig` singleton that:
1. Loads `.env` variables via `python-dotenv`
2. Reads `APP_ENV` to select a YAML config file
3. Provides `get_config("jira.timeout")` with dot-notation access
4. Uses exponential backoff retry for config loading

## Presentation Layer (`src/app/presentation/cli.py`)

A thin **shell** built with **Typer** and **InquirerPy**. It wires registered commands to feature presentation handlers but contains no business logic:

```python
app = typer.Typer(no_args_is_help=False)

@app.command("fetch-epic")
def fetch_epic_command(issue_id: str):
    """Fetch an epic and its stories from Jira by key."""
    fetch_epic(issue_id)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        show_welcome_message()
        interactive_menu()
```

Direct commands delegate to `src/app/features/epic/presentation/commands.py`, which resolves repositories through the feature composition roots (`get_epic_repository()`, `get_story_repository()`). When invoked without a command, the interactive menu takes over.

## Shared Layer (`src/app/shared/`)

Cross-cutting utilities independent of business logic.

#### Logging (`logging.py`)

Centralized structured logging with request-correlation context. Emits single-line JSON by default (dev/prod) or human-readable plain text for local/container runs, selected via the `format_type` key in the environment YAML config (`text` or `json`). Correlation IDs (`request_id`, `user_id`) are injected into every record via context variables. Callers obtain a logger with `get_logger(__name__)`; `AppConfig` calls `initialize_logging()` at startup.

#### Utilities (`utils/`)

Reusable helpers: `retry_decorator` (exponential backoff for transient failures). Used by config loading and repository operations.

## Dependency Injection

Manual (no DI framework). Each feature owns its composition root in `infrastructure/dependencies.py`:

```python
def get_epic_repository() -> JiraEpicRepository:
    return JiraEpicRepository(JiraSettings.from_config())

def get_story_repository() -> JiraStoryRepository:
    return JiraStoryRepository(JiraSettings.from_config())
```

Use cases receive ports through constructor injection; presentation handlers resolve concrete adapters through these factories.

## DDD Patterns in Use

| Pattern | Where | Why |
|---------|-------|-----|
| **Vertical Slice** | `features/epic/`, `features/story/` | Cohesion by capability; change one feature without touching the other |
| **Shared Kernel** | `core/domain/` | Single home for concepts every feature needs |
| **Factory Method** | `Epic.create()`, `UserStory.create()` | Ensures all invariants are checked before the object exists |
| **Value Object** | `IssueId`, `Priority`, `StoryPoints`, `Label` | Immutable, self-validating, equality by value |
| **Repository (Port)** | `EpicRepository`, `StoryRepository` ABCs | Decouple features from infrastructure |
| **Entity** | `Epic`, `UserStory` | Objects with identity and lifecycle |
| **Domain Exception** | `EntityNotFoundException`, etc. | Business-meaningful errors, not generic exceptions |
| **DTO** | `EpicDtoResponse`, `StoryDtoResponse` | Clean boundary between layers |
| **Mapper** | `EpicDataMapper`, `StoryDataMapper` | Transform between layers without leaking concerns |
| **Composition Root** | Per-feature `dependencies.py` | Single place wiring ports to adapters |

## Testing Architecture

Tests mirror the source structure — one test tree per slice:

```
tests/
├── unit/
│   ├── core/
│   │   └── domain/              # Value objects, exceptions, issue abstractions
│   ├── features/
│   │   ├── epic/
│   │   │   ├── domain/          # Epic factory method tests
│   │   │   ├── application/     # Use case tests with mocked ports
│   │   │   ├── infrastructure/  # Project-key restriction tests
│   │   │   └── presentation/    # Command handler tests
│   │   └── story/
│   │       ├── domain/          # UserStory factory method tests
│   │       └── application/     # Mapper tests
│   ├── presentation/            # Typer command registration tests
│   └── shared/                  # Logging tests
└── integration/
    ├── epic/                    # JiraEpicRepository with respx mocking
    └── story/                   # JiraStoryRepository with respx mocking
```

Use case tests mock the repository **ports**. Adapter tests use `respx` to mock HTTP responses against the real repository implementations.
