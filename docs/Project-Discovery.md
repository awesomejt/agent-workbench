# Project Discovery Config

How the workbench discovers and registers projects from local directory trees.

## Design Intent

Project discovery is a post-MVP feature — the MVP relies on projects being registered manually via `awb project create` or the API. This document defines the configuration format and discovery rules so the feature can be implemented consistently when it is built.

## Config File Location

Discovery config lives in `~/.config/awb/discovery.yaml` (preferred) or `~/.config/agent-workbench/discovery.yaml`. This is the same config search path used by the `awb` CLI for connection settings.

A project-local override may also be placed at `<project-root>/.awb.yaml` to customise how that specific project is registered.

## Discovery Config Format

```yaml
# ~/.config/awb/discovery.yaml

discovery:
  # Directories to scan for project roots.
  # Tilde-expanded; relative paths are resolved from $HOME.
  paths:
    - ~/projects/ai
    - ~/projects/courses
    - ~/projects/dev
    - ~/projects/infra

  # Files/directories that mark a project root when found.
  # The first match wins — deeper directories are not scanned for sub-projects.
  markers:
    - AGENTS.md
    - .git

  # Directories to skip at any depth.
  exclude:
    - .git
    - node_modules
    - .venv
    - __pycache__
    - dist
    - build

  # Maximum directory depth to search below each root path (0 = flat).
  max_depth: 2

  # Default project_type when none can be inferred.
  default_type: code

  # Path-prefix type hints: if a discovered project's path starts with
  # the prefix (after tilde expansion), apply the given type as default.
  # Explicit AGENTS.md or .awb.yaml settings override these.
  type_hints:
    ~/projects/ai: code
    ~/projects/courses: course
    ~/projects/dev: code
    ~/projects/infra: infrastructure
```

## Discovery Behaviour

1. For each path in `discovery.paths`, walk the directory tree up to `max_depth` levels deep.
2. A directory is a project root if any file/directory in `markers` is found directly inside it.
3. When a root is found, do not recurse further into it (no nested projects).
4. Skip any directory matching an entry in `exclude`.
5. Infer `project_type` by checking path-prefix type hints; fall back to `default_type`.
6. Check whether a project with the same slug (derived from directory name) already exists in the API; skip if already registered, update if local_path differs.

## Per-Project Override

An optional `.awb.yaml` file at a project root can set project-specific registration values:

```yaml
# <project-root>/.awb.yaml
name: My Project
slug: my-project
project_type: course
default_agent: claude-local
```

Fields not set here are inferred from the directory or the global discovery config.

## Slug Derivation

When no explicit slug is provided:

1. Take the directory name.
2. Lowercase, replace spaces and underscores with hyphens.
3. Strip leading/trailing hyphens.
4. Truncate to 64 characters.

Example: `~/projects/dev/agent-workbench` → slug `agent-workbench`.

## CLI Command (Post-MVP)

```bash
# Dry-run: show what would be registered without creating anything
awb project discover --dry-run

# Register all discovered projects
awb project discover

# Limit to one path
awb project discover --path ~/projects/dev
```

## Registration Logic

For each discovered project, the discovery command:
1. Checks if a project with the derived slug already exists.
2. If not: calls `POST /api/projects` to create it with inferred fields.
3. If exists and `local_path` differs: calls `PATCH /api/projects/{id}` to update `local_path`.
4. Prints the action taken for each project.

Discovery is idempotent — running it twice should produce the same state.
