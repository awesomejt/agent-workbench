# HashiCorp Vault Research

Research findings on HashiCorp Vault integration for Agent Workbench deployment
secrets. Current state: secrets are injected via Docker Compose env files and
Ansible-managed variables. Vault is a future candidate for dynamic secrets,
audit logging, and lease management.

## Context

The current secrets model (from `docs/Secrets.md`):
- Local dev: `api/.env` (gitignored, developer-managed)
- Dev/stage/prod: env files or Compose secrets on the VM, sourced from Ansible
- Credential rotation: manual

Pain points that motivate Vault:
1. Static database passwords — if a password leaks, every deployment must be
   updated manually.
2. No audit log for secret access — no record of when `DATABASE_URL` was read.
3. Manual rotation — changing a DB password requires touching multiple files
   across multiple VMs.
4. No short-lived credentials — agents and services hold long-lived passwords.

---

## What Vault Provides

**Dynamic secrets** — Vault generates a unique, short-lived PostgreSQL username
and password on demand. When the lease expires, Vault revokes the credential at
the database. No static passwords to rotate; a compromised credential expires
within minutes to hours.

**Audit log** — every secret read, lease renewal, and revocation is written to
a structured log. Useful for compliance or diagnosing a breach.

**Lease management** — Vault clients renew leases while active and surrender
them on shutdown. The API container requests a credential at startup, renews it
periodically, and Vault revokes it when the container stops.

**Secret namespacing** — separate paths for each environment (`secret/local`,
`secret/dev`, `secret/prod`), each with its own policy.

---

## Integration Patterns

### Pattern 1: Vault Agent Sidecar

A Vault Agent container runs alongside the API container. At startup it
authenticates to Vault (AppRole or Kubernetes auth), fetches the database
credential, writes it to a shared file or env var, and renews the lease
automatically.

```yaml
# compose.yaml (conceptual)
services:
  vault-agent:
    image: hashicorp/vault:1.17
    command: agent -config=/vault/config/agent.hcl
    volumes:
      - vault-secrets:/vault/secrets
  api:
    env_file: /vault/secrets/agent-workbench.env  # written by vault-agent
    volumes:
      - vault-secrets:/vault/secrets
```

**Pros:** API container has no Vault dependency in application code; the env
file pattern is identical to the current model.

**Cons:** requires a running Vault Agent sidecar for every API deployment,
adds container orchestration complexity.

### Pattern 2: Direct API Call at Startup

The API container calls the Vault HTTP API directly on startup to fetch its
database credential, then constructs `DATABASE_URL` from the response.

```python
# api/src/agent_workbench/vault.py
import os, requests

def load_db_url_from_vault():
    vault_addr = os.environ["VAULT_ADDR"]
    vault_token = os.environ["VAULT_TOKEN"]  # or AppRole secret-id
    resp = requests.get(
        f"{vault_addr}/v1/database/creds/agent-workbench",
        headers={"X-Vault-Token": vault_token},
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    host = os.environ["DB_HOST"]
    return f"postgresql+psycopg://{data['username']}:{data['password']}@{host}/agent_workbench"
```

**Pros:** no sidecar needed, works with existing Docker Compose topology.

**Cons:** credential renewal requires application-level logic (background
thread or pre-request hook); more code to maintain.

### Pattern 3: Vault-Injected Env File (Envconsul / Vault Agent Template)

Vault Agent with `template` stanza renders an env file from Vault secrets
before the API process starts. The agent process then `exec`s the API server
with the env file loaded. This is a common pattern for non-Kubernetes
deployments.

```hcl
# vault-agent.hcl
template {
  contents = <<-EOT
    DATABASE_URL="postgresql+psycopg://{{ with secret "database/creds/agent-workbench" }}{{ .Data.username }}:{{ .Data.password }}{{ end }}@{{ env "DB_HOST" }}/agent_workbench"
  EOT
  destination = "/vault/secrets/env"
  command     = "systemctl reload agent-workbench-api"  # or kill -HUP
}
```

**Pros:** cleanest for systemd-managed deployments; the application never
talks to Vault.

**Cons:** adds Vault Agent as a required system process alongside the
application.

---

## Vault Setup Requirements

### Infrastructure

- **Vault server**: one instance is sufficient for a homelab. Can run in
  Docker Compose on a dedicated VM or as a systemd service.
- **Storage backend**: Integrated Raft storage (no external Consul dependency)
  is the recommended choice for a single-node homelab setup.
- **TLS**: required in production. A self-signed cert or a cert from a local
  CA (e.g., `step-ca`) is appropriate for the homelab.

### Authentication Methods

| Method | Suitable for | Notes |
|---|---|---|
| `AppRole` | Services / automated jobs | Role ID + Secret ID; Secret ID is short-lived |
| `Token` | Local dev / initial setup | Simple but requires manual rotation |
| `Kubernetes` | K3s deployment | Vault reads K8s service account JWT |
| `AWS IAM` | Cloud workloads | Not applicable here |

For Docker Compose: AppRole is the right choice. The role ID is non-sensitive
(can be stored in the Compose env file); the secret ID is injected at deploy
time from Ansible.

For K3s (future): Kubernetes auth eliminates the need to manage AppRole secret
IDs.

### PostgreSQL Secrets Engine

```bash
# Enable the database secrets engine
vault secrets enable database

# Configure the PostgreSQL connection
vault write database/config/agent-workbench \
  plugin_name=postgresql-database-plugin \
  allowed_roles="agent-workbench" \
  connection_url="postgresql://{{username}}:{{password}}@postgresql.taylor.lan/agent_workbench" \
  username="vault-admin" \
  password="<static-admin-password-only-vault-knows>"

# Create a role with a 1-hour credential TTL
vault write database/roles/agent-workbench \
  db_name=agent-workbench \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT agent_workbench_role TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

---

## Proposed Migration Path

### Step 1 (current): Compose env files and Ansible secrets

No change. This is working and sufficient for the initial deployment.

### Step 2 (MVP+1): Vault for static secrets only

Run Vault in Compose alongside the API. Use the KV secrets engine (not dynamic
secrets). This establishes the Vault deployment and AppRole auth without
changing the PostgreSQL credential model.

```bash
vault kv put secret/agent-workbench/prod \
  DATABASE_URL="postgresql+psycopg://agent_workbench:$(cat /run/secrets/db_pass)@postgresql.taylor.lan/agent_workbench" \
  SECRET_KEY="$(openssl rand -hex 32)"
```

Vault Agent renders these to `/vault/secrets/env` at container start.

### Step 3 (post-MVP): Dynamic PostgreSQL credentials

Replace the static `DATABASE_URL` with a Vault-generated credential using the
PostgreSQL secrets engine. Requires creating a `vault-admin` PostgreSQL user
with the `CREATEROLE` privilege.

### Step 4 (K3s): Kubernetes auth

Replace AppRole with Vault's Kubernetes auth method. The K3s pod's service
account JWT authenticates to Vault directly. No secret IDs to manage.

---

## Resource Requirements (Homelab)

| Component | Typical RAM | Notes |
|---|---|---|
| Vault server (Raft) | 128–256 MB | Single node |
| Vault Agent sidecar | 32–64 MB | Per service that uses Vault |
| PostgreSQL `vault-admin` user | — | DB-side only |

Total overhead for two Vault-integrated services: ~350 MB RAM. Acceptable on
a homelab with 8+ GB RAM.

---

## Recommendation

1. **Do not implement Vault now.** The current Compose env file + Ansible
   model is working, low-complexity, and appropriate for a one-user private LAN.

2. **Document the migration path** (this document) so the path is clear when
   the complexity is warranted.

3. **Vault becomes worthwhile when any of these is true:**
   - A second person or service needs access to production secrets.
   - A security incident makes manual password rotation painful.
   - K3s deployment begins (Kubernetes auth makes Vault's overhead much lower).
   - Compliance/audit logging of secret access is required.

4. **When ready, start with Step 2** (Vault KV for static secrets, no dynamic
   credentials) to validate the deployment before adding the PostgreSQL secrets
   engine complexity.

---

## Open Questions

- **Vault HA**: a single-node Raft Vault is acceptable for the homelab but is
  a single point of failure. The sealed-on-restart behavior means a manual
  unseal step (or auto-unseal via a cloud KMS) is needed after reboots.
- **Auto-unseal**: HashiCorp offers cloud KMS auto-unseal (AWS, GCP, Azure) but
  these require cloud accounts. For a fully local setup, Transit auto-unseal
  from a second Vault is an option but adds complexity.
- **Backup**: Vault Raft snapshots must be taken and stored outside the Vault
  node. Integrate with existing Ansible backup playbooks.
- **`vault-admin` PostgreSQL privileges**: the admin user needs `CREATEROLE`
  and the ability to grant roles. This is a more privileged user than
  `agent_workbench`; its password must be stored securely (and is a good
  candidate for Vault's own KV store once bootstrapped).
