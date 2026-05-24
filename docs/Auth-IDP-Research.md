# Authentication and IDP Research

Research findings on authentication and identity provider options for Agent
Workbench post-MVP. The current MVP runs on a private LAN without
authentication; this document informs the decision when that changes.

## Context and Constraints

**What we are protecting:**

- The Agent Workbench REST API (task coordination, run records, events)
- A future web UI (human-facing project and task browser)

**Who the users are:**

- **Jason** — one human operator, via web UI and CLI
- **AI agents** — `awb` CLI and direct HTTP calls; may run unattended on a
  schedule

**Deployment constraints:**

- Self-hosted on a private homelab LAN; no public internet exposure for MVP
- Docker Compose on a VM today; K3s on Proxmox as a future target
- No existing IDP infrastructure; anything chosen must be self-hosted

**Non-requirements at MVP+1:**

- Multi-tenant access; Jason is the only human operator
- Social login (GitHub, Google); a local user store is fine
- SAML; OIDC is sufficient

---

## Auth Pattern Options

### Option A: API Keys (agents) + Session Cookies (web UI)

The simplest viable model. The API accepts:
- `Authorization: Bearer <api-key>` for programmatic access (agents, `awb`)
- Session cookie from a login form for the web UI

API keys are stored as hashed values in the database (same pattern as
`SECRET_KEY`-signed tokens or UUID keys with bcrypt hashes). No IDP needed;
auth logic lives entirely in the Flask app.

**Pros:** no external dependency, trivial to implement, fits the private-LAN
threat model, easy to automate (agents just need an env var).

**Cons:** no SSO, no 2FA, manual key rotation, no delegated token issuance.
Does not compose well if more apps are added to the homelab later.

### Option B: Reverse Proxy Forward Auth (Authelia / Traefik)

Place Authelia in front of the API behind a Traefik reverse proxy. Authelia
handles browser sessions and 2FA; the proxy injects an `X-Remote-User` header
into upstream requests. The API trusts this header when running behind the proxy.

Agents bypass Authelia via direct API access with a shared secret or API key
(Authelia allows per-path bypass rules).

**Pros:** SSO across all homelab apps, 2FA out of the box, no code changes in
Flask for human auth, lightweight (single Go binary).

**Cons:** adds a mandatory Authelia + Redis container dependency, forward-auth
pattern only works behind Traefik/nginx (not for direct CLI access), must
maintain bypass rules for agent paths.

### Option C: Full OIDC IDP (Authentik or Zitadel)

A full-featured OIDC server that issues JWTs. Flask validates tokens with
`python-jose` or `authlib`. The CLI uses device flow or a long-lived API key
issued from the IDP. The web UI uses the authorization code flow.

**Authentik:** Python/Django-based, extensive features (flows, policies, LDAP,
SCIM), web admin UI. Higher resource use (~500 MB RAM), more complex initial
setup.

**Zitadel:** Go-based, cloud-native, designed for Kubernetes, strong machine
user / API key support. Lighter than Authentik but less mature for single-VM
Compose deployments.

**Pros:** standards-compliant, composable with other apps, long-lived machine
tokens are first-class citizens (good for agents), audit log built in.

**Cons:** heaviest option, adds significant ops overhead for a one-user
homelab, initial setup is non-trivial.

### Option D: Lightweight OIDC Bridge (Dex)

Dex is a minimal OIDC provider (Go binary, ~50 MB RAM) that bridges to
upstream identity sources (static passwords, GitHub OAuth, LDAP). It issues
JWTs; Flask validates them.

Machine clients (agents) use the client credentials grant with a static secret.
Human login uses a browser flow backed by a static password or GitHub OAuth.

**Pros:** very lightweight, standards-based JWTs, machine credential support is
clean, composes well.

**Cons:** limited web admin UI (config is YAML-file-driven), less active
maintenance than Authentik/Zitadel, more manual config than Authelia.

---

## Comparison Summary

| Option | Complexity | Agent auth | Human auth | Self-hosted ops | Composes with other apps |
|---|---|---|---|---|---|
| A: API keys + session | Low | API key env var | Form login | None | No |
| B: Authelia forward auth | Medium | Bypass rules + shared secret | 2FA browser session | Authelia + Redis | Yes (Traefik) |
| C: Authentik / Zitadel | High | Machine user / API key | OIDC browser flow | Full IDP stack | Yes (OIDC) |
| D: Dex | Medium | Client credentials JWT | OIDC browser flow | Single binary | Yes (OIDC) |

---

## Recommendation

**Phase 1 (MVP+1, private LAN only):** Option A — API keys + session cookies.

This is the right first step because:
- The threat model does not justify a full IDP on a private LAN accessible only
  to Jason and his agents.
- Implementation is entirely inside Flask; no new services to operate.
- Agent workflows do not change: set `AWB_API_KEY=<key>` in the environment.
- Reversible: API keys can be kept as an agent-auth mechanism even after an IDP
  is added for human access.

**Phase 2 (if other homelab apps are added or access is broadened):** Option B
or Option D.

- Choose **Authelia** if the priority is protecting web UIs with 2FA and
  minimal code changes. Good fit if Traefik is already the reverse proxy.
- Choose **Dex** if JWT-based standards compliance matters (e.g., the
  workbench API will be called from a broader set of clients or environments).
  Dex's machine credential model (client credentials grant) maps cleanly onto
  agent use.

Authentik or Zitadel are appropriate only if multi-app SSO, SCIM provisioning,
or organization-level policy enforcement are needed. That is not the current
trajectory.

---

## Flask Integration Sketch (Option A)

```python
# api/src/agent_workbench/auth.py

from functools import wraps
from flask import request, abort, g
from .models import ApiKey  # hashed key table

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer(request)
        if not token:
            abort(401)
        key = ApiKey.verify(token)  # timing-safe hash compare
        if not key:
            abort(401)
        g.actor = key.actor_name
        return f(*args, **kwargs)
    return decorated

def _extract_bearer(req):
    header = req.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None
```

The `ApiKey` table would hold:
- `id`, `key_hash` (bcrypt), `actor_name`, `description`, `created_at`,
  `last_used_at`, `expires_at` (nullable), `revoked_at` (nullable)

API key creation is a CLI command or admin endpoint behind a bootstrap secret
(or simply set directly in the database for the initial deployment).

---

## Agent Workbench Changes Required (Option A)

1. Add `api_keys` table + Alembic migration.
2. Add `require_auth` decorator; apply to all API routes.
3. Add `--api-key` flag / `AWB_API_KEY` env var to `awb` CLI; send as
   `Authorization: Bearer` header.
4. Update `docs/Secrets.md` with key generation and rotation guidance.
5. Add `AWB_API_KEY` to `.env.example` with a placeholder value.
6. Update integration tests to pass a test API key in the `AWB_API_URL`
   environment.

---

## Open Questions

- **Key bootstrap**: how is the first API key created? Options: migration seed
  for local dev, CLI subcommand, or a one-time setup endpoint guarded by a
  bootstrap token.
- **Key rotation**: when a key is rotated, all agents that use it need the new
  value. Proposed: overlap window where both old and new key are valid for a
  configurable period.
- **CI/CD**: integration tests currently call the API without auth. Tests will
  need a fixture that creates (or seeds) a test key. This is a breaking change
  for the test suite.
