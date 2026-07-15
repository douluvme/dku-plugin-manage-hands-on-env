# Changelog

All notable changes to this plugin are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/). `plugin.json`
keeps a one-line summary per version; this file has the details.

## [1.1.0]

### Added
- `SECURITY.md` documenting credential handling and the June-July 2026
  incident remediation checklist (AWS key rotation still pending).

### Fixed
- `duplicate_project_by_id` no longer overwrites the `duplicated` tag with
  just the project name; returns `None` (not `""`) on failure.
- Leading/trailing blank-line formatting in `2-1-delete-starter-projects`
  results.
- Crash (`UnauthorizedException`/`NotFoundException`) when deleting nested
  folders in "all user folders" mode, caused by re-listing a folder's
  children after some had already been deleted earlier in the same run.
- `KeyError: 'build_TF'` crash in `1-1-duplicate-starter-projects`, caused
  by dead `build_TF`/`build_all` wiring left over from a disabled feature.

### Removed
- Deprecated `[OLD] 2-1-delete-starter-projects` runnable.
- `build_TF` parameter and call sites (the `build_all()` function itself
  is kept in `common_functions.py` for potential future use, but is no
  longer wired into any runnable).

## [1.0.9]

### Added
- Delete everything from all user folders option.

## [1.0.8]

### Changed
- Various changes to duplicate, delete, and change ownership macros.

## [1.0.7]

### Added
- Loan advisor agent starter.

## [1.0.6]

### Added
- Functionality to delete project in sandbox folder.

## [1.0.5]

### Added
- Agent hands-on projects.

## [1.0.4]

### Added
- Functionality to disable a deployment before deleting it, to prevent
  leaving ghost services on API nodes.
