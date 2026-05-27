---
type: project
status: draft
name: "My Project"
slug: my-project
project_type: code
local_path: /shared/projects/dev/my-project
git_remote_url: ""
environment: local
default_agent: ""
---

Optional notes about this project. This body is not sent to the API — it is
for your own reference only.

Leave status as "draft" while you are still writing. Change it to "ready" when
the project definition is complete and should be registered on the next onboard run.

The onboarding tool ignores *.template.md files, so this file is safe to keep
in the onboarding/ folder as a reference.

Projects are processed before tasks in the same run, so you can include both
a project file and task files in one batch and they will be created in the
correct order.

## Front matter reference

| Field         | Required | Values / notes                                                              |
|---------------|----------|-----------------------------------------------------------------------------|
| type          | yes      | project                                                                     |
| status        | yes      | draft · ready · processed                                                   |
| name          | yes      | human-readable display name                                                 |
| slug          | yes      | URL-safe identifier, unique across the workbench (lowercase, hyphens)       |
| project_type  | no       | code · course · content · research · infrastructure · other (default: code) |
| local_path    | no       | absolute path to the project on disk                                        |
| git_remote_url| no       | remote Git URL (e.g. https://github.com/org/repo)                          |
| environment   | no       | local · dev · stage · prod (default: local)                                 |
| default_agent | no       | name of the agent that works this project by default                        |

After onboarding, the tool adds these fields automatically:
  project_id:   UUID of the created project
  processed_at: ISO 8601 timestamp
