# trader-data

Trade Nexus Data Module repository.

## Gate0 bootstrap scope

- Establish ownership and module boundaries.
- Keep implementation endpoint-free in Gate0.
- Provide adapter-first interfaces and contract guardrail tests.

## Contract boundary

- External consumers must go through Platform API only.
- Public API source of truth remains in `trade-nexus` OpenAPI spec.
Trade Nexus data module repository
