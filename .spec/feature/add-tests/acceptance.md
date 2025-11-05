- AC-1: `pytest --cov=src` exits 0 with line coverage ≥80% (Status: At risk – current coverage 78%).
- AC-2: Aggregated totals from `discover_and_run_checkers` match the sum of mocked checker returns (Status: Complete).
- AC-3: Checker-specific fixtures execute without unexpected exceptions while producing result files or empty outputs as designed (Status: Complete).
Test Strategy: unit, integration
Coverage Target: lines 80%, branches 70%
