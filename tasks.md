# Tasks

## Review Backlog

### PR #99 — Add NCMARM001 unauthorized permission escalation checker (2026-05-04)

- [ ] [debt] `download_reason_checker._load_access_logs`:
      `drop_duplicates(inplace=True)` applied to cache copy only —
      first caller deduplicates, subsequent callers receive duplicates
      (source: Claude Code) — `src/checkers/download_reason_checker.py:146`
- [ ] [debt] `_load_allowlist` return type: use `frozenset[str]` instead of
      `set[str]` to signal immutability (source: Claude Code) —
      `src/checkers/ncmarm001_checker.py:49`
- [ ] [doc] Module docstring says "승인 없는 권한 상승" (spaces) but config
      constant `NCMARM001_UNAUTHORIZED_GRANT_SUFFIX` has no spaces —
      clarify intent in docstring (source: Claude Code) —
      `src/checkers/ncmarm001_checker.py:6`, `src/config.py:77`
- [ ] [constraint] No test verifying all names in `CHECKER_ORDER` correspond
      to existing checker modules — silent drift risk when checkers are
      added/removed (source: Claude Code) — `src/main.py:47-52`
