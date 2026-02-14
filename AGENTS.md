# AGENTS.md

## Repository Purpose

`trader-data` is the Trade Nexus data/knowledge module repository.

## Boundary Rules

1. No external client entrypoints are exposed directly from this repo.
2. Internal service routes are allowed only under `/internal/v1/*` with service auth.
3. External clients must consume data capabilities through Platform API.
4. Provider API integrations remain adapter-scoped.

## Development Rules

1. Keep interfaces typed and adapter-first.
2. Add boundary tests for contract-sensitive behavior.
3. Include tenant/user/request identity context in cross-boundary calls.
