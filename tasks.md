# Tasks

status: active

## Review Backlog

### PR #99 — Add NCMARM001 unauthorized permission escalation checker (2026-05-04)

- [x] [debt] `_load_allowlist`: use `frozenset[str]` — commit 354a583
- [x] [doc] Clarify NCMARM001 docstring suffix — commit 60b4c6e
- [x] [constraint] CHECKER_ORDER drift guard test — commit 43b52d2
- ~~[debt] `download_reason_checker._load_access_logs`: dedup on cache copy~~
  *Resolved by refactor #106: `load_merged_excel` replaces cached path;
  `drop_duplicates` now on fresh frame — no fix needed.*

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
