# Changelog

All notable changes to DevWorkWire are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-26

### Added

- `WorkItemProvider` port: single provider boundary for all work-item
  operations, replacing per-feature `EpicRepository` and `StoryRepository`.
- `JiraWorkItemProvider`: merged Jira adapter implementing the unified port.
- `ProjectConfig`: loads `devworkwire.yml` with provider selection, project key,
  and field mappings (`story_points` custom field configurable via config).
- `--config` CLI option to point `dwire` at a custom `devworkwire.yml` path.
- `devworkwire.example.yml` documenting all available project config fields.
- Port-contract, config-loader, and field-mapping tests.

### Changed

- `JiraSettings` no longer carries `project_key`; project selection is now
  entirely owned by `ProjectConfig` (`devworkwire.yml`).
- Use cases (`CreateEpicFromMarkdown`, `GetEpicWithStories`) now depend on
  `WorkItemProvider` instead of separate repository ports.
- Composition root wires `WorkItemProvider` from `JiraSettings` +
  `ProjectConfig`, selecting the adapter by `provider` field.

### Removed

- `EpicRepository` and `StoryRepository` feature-level port ABCs.
- `JiraEpicRepository` and `JiraStoryRepository` (replaced by the unified
  `JiraWorkItemProvider`).
- Dead speculative methods (`get_user_story`, `create_story`,
  `update_story_status`) that never had a use case calling them.

## [0.1.0] - 2026-08-26

### Added

- Proper Python packaging: `pyproject.toml` with project metadata, runtime and dev
  dependencies, and the `dwire` console script entry point.
- Editable-install development flow (`pip install -e ".[dev]"`).

### Changed

- **Renamed the project from Story Flow Engine to DevWorkWire** (package
  `devworkwire`, CLI command `dwire`), per `specs/devworkwire-plan.md`.
- Source package moved from `src/app/` to `src/devworkwire/`; all imports updated.
- Documentation, CLI banner, and configuration files updated to the new identity.
