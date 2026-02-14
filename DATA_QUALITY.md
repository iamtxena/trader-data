# Data Quality

## Minimum checks

1. Timestamp monotonicity.
2. Required field presence.
3. Numeric range sanity checks.
4. Duplicate/outlier detection policy.

## Operational policy

- Failed quality checks are logged with request context.
- Critical violations block promotion of affected datasets.
