# AGENTS.md

## Repository Purpose

`trader-data` is the Trade Nexus data/knowledge module repository.

## Boundary Rules

1. No external client entrypoints are exposed directly from this repo in Gate0.
2. External clients must consume data capabilities through Platform API.
3. Provider API integrations remain adapter-scoped.

## Development Rules

1. Keep interfaces typed and adapter-first.
2. Add boundary tests for contract-sensitive behavior.
3. Include tenant/user/request identity context in cross-boundary calls.
