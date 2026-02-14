# Data Model

## Canonical market data schema (v1.0)

1. `TickV1`
- Fields: `schema_version`, `symbol`, `exchange`, `event_time`, `price`, `quantity`, `side`, `trade_id`.
2. `OrderBookSnapshotV1`
- Fields: `schema_version`, `symbol`, `exchange`, `event_time`, `bids[]`, `asks[]`.
3. `CandleV1`
- Fields: `schema_version`, `symbol`, `exchange`, `interval`, `open`, `high`, `low`, `close`, `volume`, `event_time`.
4. `ContextualCandleV1`
- Fields: `schema_version`, `candle`, `sentiment`, `regime`, `news[]`, `custom{}`.

## Constraints

1. Schema version is fixed at `1.0` for all canonical types in this wave.
2. Internal routes must stay under `/internal/v1/*` and require service auth.
3. External clients must continue to use Platform API (`trade-nexus`) only.
4. Ingestion and transform pipelines must be deterministic for identical input payloads/configuration.
