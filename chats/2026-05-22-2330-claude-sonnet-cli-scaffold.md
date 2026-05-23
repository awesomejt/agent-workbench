# Session: Go CLI Scaffold + Benchmark Decision
**Date:** 2026-05-22  
**Agent:** claude-sonnet-4-6 (session 6)  
**Commit:** `611321f`

## Summary

Recorded benchmark API discussion and decision, then scaffolded the Go CLI (`awb` binary).

## Decisions

- **Benchmark split**: Lightweight runtime metrics (`model_id`, token counts, `latency_ms`, `prompt_category`) belong on the `runs` table in agent-workbench to inform lease tuning and model selection. A separate `benchmark-harness` project handles structured evaluation (prompt libraries, scoring rubrics, comparison reports). Both recorded in MEMORY and TODO.
- **CLI module path**: `agent-workbench/cli` — update to VCS path when GitHub remote is added.
- **CLI binary name**: `awb` — short, unambiguous.
- **Config resolution order**: `--flag` > `AWB_*` env var > `~/.config/agent-workbench/config.yaml`.

## CLI Structure

```
cli/
  main.go
  go.mod / go.sum          (Go 1.26, Cobra v1.10.2, Viper v1.21.0)
  cmd/
    root.go                persistent flags: --api-url, --project, --agent, --output
    version.go             awb version
    project.go             awb project list
    status.go              awb status show
    task.go                awb task list / get / next
    task_claim.go          awb task claim <id>
    task_heartbeat.go      awb task heartbeat <id>
    task_complete.go       awb task complete <id>
    task_block.go          awb task block <id>
  internal/
    api/client.go          HTTP client (all API calls)
    api/types.go           Response types matching Flask _serialize output
    output/output.go       JSON and table formatters
```

## Key Implementation Notes

- `task claim --duration 0` (default) omits `duration_seconds` from the request body, letting the server use `task.estimated_duration_seconds` or its 1800s default.
- `task next` fetches the first pending task ordered by priority from the API — no dedicated endpoint needed.
- `project list` is used internally by commands that need a project UUID from a slug.
- `--output json` on any command returns the raw API response pretty-printed; useful for agent automation.
- `go vet ./...` passes clean.

## Makefile Targets Added

- `make build-cli` → builds `cli/builds/awb`
- `make cli-tidy` → `go mod tidy`
- `make cli-vet` → `go vet ./...`

## Next Session

- Cloud review gate (all 9 review items in TODO Review section).
- After review: runs metrics fields, README update, docs.
