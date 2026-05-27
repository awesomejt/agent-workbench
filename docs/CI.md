# CI/CD

Continuous integration for Agent Workbench runs on a self-hosted GitHub
Actions runner backed by a local Harbor registry. No external compute or
network access to the homelab is required.

---

## Runner

A self-hosted Actions runner is installed on the compose VM (or a
dedicated CI VM once K3s is running). The runner binary polls GitHub
outbound — no inbound ports or firewall changes needed.

**Host requirements:** Docker Engine + Compose v2, runner binary (systemd
service). Nothing else. All build tools are pulled as container images.

Workflow jobs use the `container:` key to execute steps inside a
purpose-built image from Harbor. The runner orchestrates the containers;
the host OS is never the execution environment.

---

## Harbor registry

Three Harbor projects are used:

| Project | Purpose | Example |
|---|---|---|
| `harbor.taylor.lan/proxy/` | Pull-through cache for DockerHub and ghcr.io | `harbor.taylor.lan/proxy/postgres:18` |
| `harbor.taylor.lan/base/` | Curated base images (ubuntu, alpine, etc.) | `harbor.taylor.lan/base/ubuntu:24.04-1` |
| `harbor.taylor.lan/ci/` | CI-focused tool images built from the base images | `harbor.taylor.lan/ci/python-uv:3.14-1` |

Using `harbor.taylor.lan/proxy/` for service containers (e.g. the
PostgreSQL test database) means every pull stays on LAN and is never
blocked by DockerHub rate limits.

---

## CI images

CI images live in a dedicated repo (`infra/homelab-images`) alongside the
Ansible repo. The `ci/` subdirectory holds purpose-built images; `base/`
holds curated upstream bases. Each image is small and single-purpose —
one image per tool chain.

```
homelab-images/
├── base/
│   ├── ubuntu/Dockerfile
│   └── alpine/Dockerfile
└── ci/
    ├── python-uv/Dockerfile   # python:3.14 + uv + pg_isready
    ├── golang/Dockerfile      # golang:1.26 + make + git
    └── node/Dockerfile        # node:24 + npm
```

### Image tagging convention

Tags follow `<upstream-version>-<build-revision>`:

```
harbor.taylor.lan/ci/python-uv:3.14-1
harbor.taylor.lan/ci/python-uv:3.14-2   # uv updated, Python unchanged
harbor.taylor.lan/ci/python-uv:3.15-1   # Python 3.15 released → revision resets
```

- The **upstream version** reflects the primary tool version (Python,
  Go, Node) — matches what you'd see on the upstream Docker Hub tag.
- The **build revision** (`-1`, `-2`, …) increments for any change to
  the image that doesn't change the upstream version: tool additions,
  uv/npm upgrades, security patches, Dockerfile fixes.
- Revision resets to `-1` whenever the upstream version bumps.

This follows the same convention as Debian package versioning and makes
the lineage readable without needing to inspect build dates.

Workflow files pin to a specific tag (e.g. `3.14-1`) and update
deliberately. Avoid `:latest` in CI — silent tool upgrades break builds
in ways that are hard to bisect.

---

## Workflow structure

Agent Workbench uses three parallel jobs, each in its own purpose-built
container. PostgreSQL runs as a `services:` container networked to the
API job automatically.

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  api:
    runs-on: self-hosted
    container: harbor.taylor.lan/ci/python-uv:3.14-1
    services:
      postgres:
        image: harbor.taylor.lan/proxy/postgres:18
        env:
          POSTGRES_DB: agent_workbench_test
          POSTGRES_USER: awb
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 3s
          --health-retries 5
    env:
      DATABASE_URL: postgresql+psycopg://awb:test@postgres/agent_workbench_test
    steps:
      - uses: actions/checkout@v4
      - run: make setup
      - run: make migrate
      - run: make validate
      - run: make test

  cli:
    runs-on: self-hosted
    container: harbor.taylor.lan/ci/golang:1.26-1
    steps:
      - uses: actions/checkout@v4
      - run: make cli-vet
      - run: make cli-test
      - run: make cli-clean-build-check

  web:
    runs-on: self-hosted
    container: harbor.taylor.lan/ci/node:24-1
    steps:
      - uses: actions/checkout@v4
      - run: npm --prefix web ci
      - run: npm --prefix web run build
```

A `make ci` target should mirror these steps locally so the workflow and
local validation cannot drift. See the Makefile for the current targets.

---

## Runner install

The runner is managed via Ansible. Once the `infra/homelab-images` repo
and runner role exist, install follows the standard Ansible playbook
pattern. Manual steps for reference:

```bash
# On the target VM
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -O -L https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-<version>.tar.gz
tar xzf actions-runner-linux-x64-<version>.tar.gz
./config.sh --url https://github.com/<org>/<repo> --token <token>
sudo ./svc.sh install && sudo ./svc.sh start
```

The registration token is generated from the repo's
Settings → Actions → Runners → New self-hosted runner page. Store it in
Vault; do not commit it.

---

## Open decisions

- Runner VM: compose VM (interim) vs dedicated CI VM (post-K3s)
- Runner labels: `self-hosted` only, or capability labels like
  `[self-hosted, linux, docker]` for future multi-runner routing
- `make ci` umbrella target: not yet implemented
