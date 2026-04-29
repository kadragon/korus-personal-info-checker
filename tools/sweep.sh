#!/bin/bash
# sweep.sh — Automated garbage collection for harness
# Usage:
#   bash tools/sweep.sh           # full sweep
#   bash tools/sweep.sh --quick   # lint only
#
# Trigger: SessionStart hook in .claude/settings.json when tools/.sweep-stamp
# is missing or older than 7 days. See docs/runbook.md.

set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(cd "$TOOLS_DIR/.." && pwd)"

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

FINDINGS=()
QUICK_MODE=false
[[ "${1:-}" == "--quick" ]] && QUICK_MODE=true

cd "$PROJ_DIR"

echo -e "${CYAN}=== Sweep ===${NC}"
echo -e "  Date: $(date '+%Y-%m-%d %H:%M')"

# ── 1. Lint scan ─────────────────────────────────────────────
echo -e "${CYAN}[1/5] Lint scan...${NC}"
lint_output=$(uv run ruff check src 2>&1) || true
if [[ -n "$lint_output" ]]; then
    FINDINGS+=("[lint] ruff found issues — run: uv run ruff check src")
    echo -e "  ${YELLOW}Issues found${NC}"
else
    echo -e "  ${GREEN}Clean${NC}"
fi

$QUICK_MODE && { echo "Quick mode — done."; exit 0; }

# ── 2. Doc drift check ──────────────────────────────────────
echo -e "${CYAN}[2/5] Doc drift...${NC}"
todo_count=$(grep -rn "TODO\|FIXME" docs/ 2>/dev/null | wc -l | tr -d ' ') || true
if [[ "$todo_count" -gt 0 ]]; then
    FINDINGS+=("[docs] $todo_count TODO/FIXME marker(s) found in docs/ — review and resolve")
fi
recent_src=$(git log --since="7 days ago" --name-only --pretty=format: -- 'src/*.py' 'src/**/*.py' 2>/dev/null | sort -u | grep -v '^$') || true
recent_docs=$(git log --since="7 days ago" --name-only --pretty=format: -- 'docs/*.md' 2>/dev/null | sort -u | grep -v '^$') || true
if [[ -n "$recent_src" && -z "$recent_docs" ]]; then
    FINDINGS+=("[docs] src/ changed in last 7 days but no docs/ updates — check if architecture.md or conventions.md needs updating")
fi
echo -e "  ${GREEN}Checked ($todo_count TODO(s) in docs/, recent src/docs drift checked)${NC}"

# ── 3. Golden principle spot-check ───────────────────────────
echo -e "${CYAN}[3/5] Golden principles...${NC}"
gp_issues=0

# GP3: No PII in logs — check for logging calls that pass raw PII column values
# Pattern: logging.*(사용자ID|IP주소|다운로드사유) directly (not in comments or strings for test fixtures)
pii_log=$(grep -rn 'logging\.' src/ 2>/dev/null | grep -E '사용자ID|IP주소|다운로드사유' | grep -v '#') || true
if [[ -n "$pii_log" ]]; then
    FINDINGS+=("[gp3-pii] Possible PII in log call — review: $pii_log")
    gp_issues=$((gp_issues + 1))
fi

# GP4: Checker contract — every checker module should have run_check
for f in src/checkers/*.py; do
    [[ "$(basename "$f")" == "__init__.py" ]] && continue
    if ! grep -q "def run_check" "$f"; then
        FINDINGS+=("[gp4-contract] $f missing run_check() — checker contract violated")
        gp_issues=$((gp_issues + 1))
    fi
done

# GP5: Output encoding — check for open(..., 'w') without utf-8-sig in utils
raw_open=$(grep -n "open(" src/utils.py 2>/dev/null | grep -v "utf-8-sig\|#") || true
if [[ -n "$raw_open" ]]; then
    FINDINGS+=("[gp5-encoding] src/utils.py has open() without utf-8-sig — verify encoding: $raw_open")
    gp_issues=$((gp_issues + 1))
fi

[[ $gp_issues -eq 0 ]] && echo -e "  ${GREEN}All golden principles pass${NC}"

# ── 4. Harness freshness ────────────────────────────────────
echo -e "${CYAN}[4/5] Harness freshness...${NC}"
harness_issues=0

# Check all docs/ files referenced in AGENTS.md exist
if [[ -f "AGENTS.md" ]]; then
    while IFS= read -r line; do
        while [[ "$line" =~ (docs/[a-zA-Z0-9_./-]+\.md) ]]; do
            doc="${BASH_REMATCH[1]}"
            if [[ ! -f "$doc" ]]; then
                FINDINGS+=("[harness] AGENTS.md references missing file: $doc")
                harness_issues=$((harness_issues + 1))
            fi
            line="${line#*"${BASH_REMATCH[0]}"}"
        done
    done < AGENTS.md
fi

# Check AGENTS.md size
agents_lines=$(wc -l < AGENTS.md | tr -d ' ')
if [[ "$agents_lines" -gt 120 ]]; then
    FINDINGS+=("[harness] AGENTS.md is $agents_lines lines (warn >120, target ≤100) — move content to docs/")
    harness_issues=$((harness_issues + 1))
fi

for key_doc in docs/architecture.md docs/conventions.md docs/workflows.md docs/delegation.md docs/eval-criteria.md docs/runbook.md; do
    if [[ ! -f "$key_doc" ]]; then
        FINDINGS+=("[harness] Missing key doc: $key_doc")
        harness_issues=$((harness_issues + 1))
    fi
done

[[ $harness_issues -eq 0 ]] && echo -e "  ${GREEN}All references valid (AGENTS.md: $agents_lines lines)${NC}"

# ── 5. Load-bearing assessment (every 4th sweep) ─────────────
echo -e "${CYAN}[5/5] Load-bearing assessment...${NC}"
STAMP_FILE="$TOOLS_DIR/.sweep-stamp"
SWEEP_COUNT=0
[[ -f "$STAMP_FILE" ]] && SWEEP_COUNT=$(cat "$STAMP_FILE" 2>/dev/null | grep "^count=" | cut -d= -f2 || echo 0)
SWEEP_COUNT=$((SWEEP_COUNT + 1))

if (( SWEEP_COUNT % 4 == 0 )); then
    echo -e "  ${YELLOW}Load-bearing assessment due (sweep #$SWEEP_COUNT)${NC}"
    echo -e "  Review references/sweep-template.md → 'Load-Bearing Assessment' for methodology"
    echo -e "  Question for each harness component: is this still compensating for a real model limitation?"
else
    echo -e "  ${GREEN}Skipped (sweep #$SWEEP_COUNT; runs on every 4th sweep)${NC}"
fi

# Update stamp
echo "count=$SWEEP_COUNT" > "$STAMP_FILE"
date '+%Y-%m-%d %H:%M' >> "$STAMP_FILE"

# ── Summary ──────────────────────────────────────────────────
echo ""
if [[ ${#FINDINGS[@]} -eq 0 ]]; then
    echo -e "${GREEN}=== Sweep clean ===${NC}"
    exit 0
fi

echo -e "${YELLOW}=== ${#FINDINGS[@]} finding(s) ===${NC}"
for f in "${FINDINGS[@]}"; do echo "  $f"; done
exit 1
