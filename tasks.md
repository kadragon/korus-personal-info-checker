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

- [x] [harness] `validate-harness.sh`: Level 3 WARN gate too strict —
  removed; WARNs advisory only
- [x] [harness] `validate-harness.sh`: Level 2 not WARN-gated —
  now consistent (neither level WARN-gated)

### PR #112 — Vectorize hot-path filters, single-pass write, calamine read (2026-06-05)

Out-of-scope review items (4 reviewers). Pre-existing or beyond this PR's scope.

- [ ] [deferred] `utils.load_access_logs_cached`: cache key `(download_dir, file_prefix)`
  ignores file mtime → stale data in long-lived (daemon/notebook) sessions. *Source:
  Antigravity (P2). Deferred: pre-existing fn; the CLI is one-shot so intra-process
  mutation can't occur. Fix later: add `tuple(os.path.getmtime(...) for f in excel_files)`
  to the key.*
- [ ] [deferred] `utils.save_excel_with_autofit`: early `return` on `ws is None` leaves an
  unstyled file (ExcelWriter `__exit__` still saves). *Source: pr-review-toolkit (P2).
  Deferred: not a regression — original `to_excel(path)` already wrote an unstyled file
  before the same return; branch unreachable post-`to_excel`. Fix later: raise, or
  `os.remove(path)` outside the context.*
