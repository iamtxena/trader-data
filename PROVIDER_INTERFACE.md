# Provider Interface

## Adapter contract

Provider integrations are implemented behind adapter interfaces under `src/trader_data/adapters/`.

### Requirements

1. Accept explicit identity context.
2. Return normalized shapes.
3. Surface typed errors for upstream handling.
