# Session: Codex Review Triage + Pre-Dogfood Planning
**Date:** 2026-05-23
**Agent:** claude-sonnet-4-6 (session 8)
**Commit:** `2de58cf`

## Summary

Reviewed Codex's full-repo code review (`chats/2026-05-22-1741-codex-cli-repo-recommendations.md`),
evaluated all 10 recommendations, triaged findings into a pre-dogfood fix list, and updated all
project docs to reflect current state. Also added CLI install script and config path improvements
from the same session.

## Decisions

- **Pre-dogfood gate**: All Codex P0–P2 fixes must be completed before registering agent-workbench
  as its own project and using `awb` to manage remaining work. The system needs to be reliable
  before it manages itself.
- **Dogfood intent confirmed**: Once P0–P2 fixes land, register agent-workbench as a project in
  the workbench and use `awb task claim/heartbeat/complete` for all remaining implementation work
  instead of editing TODO.md directly.
- **Codex review accepted as cloud review gate**: Codex reviewed the full repo with live validation
  runs (`go vet`, `ruff`, `mypy`, `pytest`, clean-clone build test). This satisfies the 8 cloud
  review gate items in TODO. Signoff item stays open until fixes are resolved.
- **CLI config path order**: `~/.config/awb/` is the preferred (shorter) path; `~/.config/agent-workbench/`
  is the fallback. Both yaml and json (and toml) are supported. The `$HOME` expansion bug in the
  original `initConfig` (literal string `"$HOME/..."` not expanded by Viper) was fixed.
- **CLI install target**: `make install-cli` / `scripts/install-awb.sh` installs to `~/.local/bin`
  if it exists, then `~/bin`, creating `~/bin` if neither exists. Warns if install dir not on PATH.

## Codex Finding Priority Triage

| Priority | Count | Summary |
|---|---|---|
| P0 — Build-breaking / crash | 4 | gitignore hides `cli/internal/output/`, nil deref on ClaimedBy, double-error print, trailing slash in api-url |
| P1 — Quality gate / product correctness | 4 | ruff format (15 files), mypy (17 errors), lease-unaware task next, env example port mismatch |
| P2 — Audit trail / reliability / API correctness | 10 | event auto-append, idempotency design, API validation gaps, CLI test targets |
| P3 — CLI surface expansion | 6 | run, event, agent, project CRUD, section, status commands; shell completion |

## Key Codex Findings (Validated)

- `cli/internal/output/output.go` is silently excluded from Git by the global `output/` rule in
  `.gitignore`. Clean clones fail to build. Fix: rename directory to `cli/internal/render`.
- `ruff format` fails on 15 Python files; `mypy` fails with 17 errors (mostly Flask-SQLAlchemy
  typing and rowcount patterns). Neither is in `make validate` yet.
- `awb task next` shows tasks that are already leased — the API `status=pending` filter does not
  exclude active leases. Needs an `available=true` filter server-side.
- Task lifecycle transitions (claim, heartbeat, complete, block) do not auto-append events;
  contradicts docs and architecture intent.
- Root `.env.example.local` uses port 5432 and a different password than `api/.env.example`
  and Docker Compose (which use port 5433).
- `task_claim.go` dereferences `*task.ClaimedBy` without a nil check; crashes on unassigned tasks.

## Next Session

Proceed with P0 fixes in order:
1. Rename `cli/internal/output` → `cli/internal/render`; update all imports; fix `.gitignore`.
2. Fix nil pointer dereference on `*task.ClaimedBy`.
3. Fix double-error printing in CLI commands.
4. Trim trailing slashes from `--api-url`.
5. Add `make cli-clean-build-check` to prevent regression.
