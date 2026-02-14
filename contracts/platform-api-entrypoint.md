# Platform API Entrypoint Contract

Gate3 rule for `trader-data`:

1. No external client endpoint is exposed from this repository.
2. Internal routes are restricted to `/internal/v1/*` and require service authentication.
3. All external client traffic must enter through Platform API in `trade-nexus`.
4. Provider API interactions remain internal to adapter implementations.

Canonical public API source:

- `/Users/txena/sandbox/16.enjoy/trading/trade-nexus/docs/architecture/specs/platform-api.openapi.yaml`
