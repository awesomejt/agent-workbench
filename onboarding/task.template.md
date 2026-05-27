---
type: task
status: draft
title: ""
project: my-project-slug
phase: discovery
role: orchestrator
model_tier: cloud
priority: 5
---

Describe the task here. This body becomes the task description in the workbench.

Leave status as "draft" while you are still writing. Change it to "ready" when
the task is complete and should be picked up on the next onboard run.

The onboarding tool ignores *.template.md files, so this file is safe to keep
in the onboarding/ folder as a reference.

## Front matter reference

| Field      | Required | Values                                                                        |
|------------|----------|-------------------------------------------------------------------------------|
| type       | no       | task (default when omitted)                                                   |
| status     | yes      | draft · ready · processed                                                     |
| title      | yes      | short task title                                                               |
| project    | yes      | project slug (must already exist in the workbench)                            |
| phase      | no       | discovery · design · implementation · testing · review (default: discovery)   |
| role       | no       | researcher · planner · implementer · writer · reviewer · tester · orchestrator |
| model_tier | no       | cloud · local (default: cloud)                                                |
| priority   | no       | integer, higher = more urgent (default: 5)                                    |

After onboarding, the tool adds these fields automatically:
  task_id:      UUID of the created task
  processed_at: ISO 8601 timestamp
