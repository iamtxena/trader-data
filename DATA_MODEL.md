# Data Model

## Core entities

1. `MarketContext`
2. `ProviderContext`
3. `Signal`
4. `NormalizedCandle`

## Constraints

1. Keep provider-specific payloads out of public-facing types.
2. Preserve explicit `tenant_id`, `user_id`, `request_id` context.
3. Document versioned schema changes before rollout.
