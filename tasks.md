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

- [x] `sync-claude-md.sh`: exit 0 + stdout marker for "created" — e3033f6
- [x] `sweep.sh`: add `[5/5]` label — d081bf1
- [x] `sweep.sh`: deduplicate findings on repeat runs — d081bf1
- [x] `reconcile-harness.py`: `append_changelog` → `open("a")` — 2afb6ed
- [x] `reconcile-harness.py`: preserve trailing newline — 2afb6ed
- [x] `validate-harness.sh`: gate Level 3 on WARN count — cf782cd

### PR #109 — harness/pr108-sweep: harness sweep and validation improvements (2026-06-02)

- [ ] [harness] `validate-harness.sh`: Level 3 WARN gate may be too strict
- [ ] [harness] `validate-harness.sh`: Level 2 not gated on WARN count
