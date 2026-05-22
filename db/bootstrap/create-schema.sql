-- Agent Workbench target schema bootstrap
--
-- Run this against the selected local/dev/stage/prod database before applying
-- application migrations, if the schema does not already exist.
--
-- This file contains no credentials. Supply the target connection through psql,
-- DATABASE_URL, Ansible, Docker Compose, or your deployment tooling.

CREATE SCHEMA IF NOT EXISTS agent_workbench;

COMMENT ON SCHEMA agent_workbench IS
    'Agent Workbench application schema for projects, tasks, agents, runs, events, and reviews';

-- Optional extension for UUID generation if the application/database layer uses
-- gen_random_uuid(). Keep this here so environments are consistent.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
