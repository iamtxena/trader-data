# Contributing to trader-data

Thanks for contributing.

## Setup

1. Use Python 3.11+ and `uv`.
2. Install/run tests:

```bash
uv run --with pytest python -m pytest tests/contract/test_boundary_contracts.py
```

## Pull Request Requirements

1. Open from a branch created off `main`.
2. Include tests for behavior changes.
3. Keep the PR linked to exactly one issue when using issue-driven delivery.
4. Ensure required CI checks pass.

## Architecture and Contract Proposals

Use issue templates in `.github/ISSUE_TEMPLATE/`:

- `contract_change.yml` for API contract proposals
- `feature_request.yml` for product-level requests
- `bug_report.yml` for defects

For breaking contract proposals, include an explicit architecture approval comment URL in the issue before merge.
