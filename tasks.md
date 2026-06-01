# Tasks

status: active

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

### PR #108 — Add level-2 harness scripts and update CI/runbook (2026-06-01)

- [ ] [harness] `sync-claude-md.sh`: exit 1 for "created" case is non-standard;
      future callers using `|| echo error` will misinterpret success as failure.
      Fix: use exit 0, emit stdout to distinguish from no-op
      (source: pr-review-toolkit:review-pr)
- [ ] [harness] `sweep.sh`: missing `[5/5]` section label — progress counter
      appears to stop at 4/5 (source: pr-review-toolkit:review-pr)
- [ ] [harness] `sweep.sh`: duplicate findings appended on repeat runs — no
      check if `## Sweep <date>` section already exists
      (source: review) — `scripts/sweep.sh:444`
- [ ] [harness] `reconcile-harness.py`: `append_changelog` uses read+overwrite;
      use `open('a')` to avoid corruption on concurrent write
      (source: review) — `scripts/reconcile-harness.py:233`
- [ ] [harness] `reconcile-harness.py`: `remove_empty_headings` drops trailing
      newline — non-POSIX file on first clean run
      (source: pr-review-toolkit:review-pr) — `scripts/reconcile-harness.py:230`
- [ ] [harness] `validate-harness.sh`: Level 3 not gated on WARN count — repo
      with 0 FAILs and many WARNs still reports Level 3
      (source: review) — `scripts/validate-harness.sh:877`
