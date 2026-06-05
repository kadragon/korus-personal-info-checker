# Out-of-scope review items — PR #112 (perf/pipeline-hotpaths)

Recorded by dev-review-cycle. Not applied in this PR (pre-existing or beyond scope).

## D. Cache key ignores file mtime → stale data in long-lived sessions
- **Source:** Antigravity (P2)
- **Where:** `src/utils.py` `load_access_logs_cached` — key is `(download_dir, file_prefix)` only.
- **Why deferred:** Pre-existing function (not introduced by this PR). The CLI (`uv run korus-checker`)
  is a one-shot process that exits after a single run, so intra-process file mutation cannot occur.
  Only relevant for hypothetical daemon/notebook reuse.
- **If addressed later:** include `tuple(os.path.getmtime(...) for f in excel_files)` in the cache key.

## E. `save_excel_with_autofit` leaves an unstyled file on `ws is None`
- **Source:** pr-review-toolkit (P2)
- **Where:** `src/utils.py` `save_excel_with_autofit` — early `return` inside the `ExcelWriter`
  context still saves an unstyled workbook on `__exit__`.
- **Why deferred:** Not a regression. The original code already left an unstyled file in this case
  (`df.to_excel(path)` wrote it before the `ws is None` return). The branch is also practically
  unreachable — `.active` is never None immediately after `to_excel`.
- **If addressed later:** raise instead of returning, or `os.remove(path)` outside the context.
