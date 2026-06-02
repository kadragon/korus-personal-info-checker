#!/bin/bash
# sweep.sh — Automated garbage collection for harness (Python/uv project)
# Usage:
#   bash scripts/sweep.sh              # full sweep
#   bash scripts/sweep.sh --quick      # lint only

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

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
lint_output=""
if ! lint_output=$(uv run ruff check src 2>/dev/null); then
    FINDINGS+=("[lint] ruff: $lint_output")
    echo -e "  ${YELLOW}Issues found${NC}"
else
    echo -e "  ${GREEN}Clean${NC}"
fi

$QUICK_MODE && { echo "Quick mode — done."; exit 0; }

# ── 2. Doc drift check ──────────────────────────────────────
echo -e "${CYAN}[2/5] Doc drift...${NC}"
recent_py=""
while IFS= read -r _line; do
    [[ -n "$_line" ]] && recent_py+="$_line"$'\n'
done < <(git log --since="24 hours ago" --name-only --pretty=format: 2>/dev/null | grep '^src/checkers/.*\.py$' | sort -u) || true
recent_py="${recent_py%$'\n'}"

if [[ -n "$recent_py" ]]; then
    echo -e "  ${YELLOW}Modified checker(s) — verify AGENTS.md checker contract still holds:${NC}"
    echo "$recent_py" | while IFS= read -r f; do echo "    $f"; done
else
    echo -e "  ${GREEN}No checker files modified in last 24h${NC}"
fi

# ── 3. Golden principle spot-check ───────────────────────────
echo -e "${CYAN}[3/5] Golden principles...${NC}"
gp_issues=0

# Check GP3: Never log PII — 사용자ID, IP주소, 다운로드사유 must not appear in log() calls
pii_in_logs=$(grep -rn --include="*.py" -E "log(ger)?\.(debug|info|warning|error|critical).*(사용자ID|IP주소|다운로드사유)" src/ 2>/dev/null || true)
if [[ -n "$pii_in_logs" ]]; then
    FINDINGS+=("[gp3-pii] PII column name in log call: $pii_in_logs")
    gp_issues=$((gp_issues + 1))
fi

# Check GP4: Checker contract — run_check must exist in all checkers
while IFS= read -r checker; do
    if ! grep -q "def run_check" "$checker" 2>/dev/null; then
        FINDINGS+=("[gp4-contract] Missing run_check in $checker")
        gp_issues=$((gp_issues + 1))
    fi
done < <(find src/checkers -name "*.py" ! -name "__init__.py" 2>/dev/null) || true

if [[ $gp_issues -eq 0 ]]; then
    echo -e "  ${GREEN}No violations${NC}"
else
    echo -e "  ${YELLOW}$gp_issues violation(s) found${NC}"
fi

# ── 4. Harness freshness ────────────────────────────────────
echo -e "${CYAN}[4/5] Harness freshness...${NC}"
harness_issues=0

# Check all files referenced in AGENTS.md exist
if [[ -f "AGENTS.md" ]]; then
    while IFS= read -r _line; do
        while [[ "$_line" =~ (docs/[a-zA-Z0-9_./-]+\.(md|txt)) ]]; do
            doc="${BASH_REMATCH[1]}"
            if [[ ! -f "$doc" ]]; then
                FINDINGS+=("[harness] AGENTS.md references missing file: $doc")
                harness_issues=$((harness_issues + 1))
            fi
            _line="${_line#*"${BASH_REMATCH[0]}"}"
        done
    done < AGENTS.md
fi

# Check key docs exist
for key_doc in docs/architecture.md docs/conventions.md docs/workflows.md docs/delegation.md docs/eval-criteria.md; do
    if [[ ! -f "$key_doc" ]]; then
        FINDINGS+=("[harness] Missing key doc: $key_doc")
        harness_issues=$((harness_issues + 1))
    fi
done

[[ $harness_issues -eq 0 ]] && echo -e "  ${GREEN}All references valid${NC}"

# ── [5/5] Summary ───────────────────────────────────────────
echo ""
if [[ ${#FINDINGS[@]} -eq 0 ]]; then
    echo -e "${GREEN}=== Sweep clean ===${NC}"
    exit 0
fi

echo -e "${YELLOW}=== ${#FINDINGS[@]} finding(s) ===${NC}"
for f in "${FINDINGS[@]}"; do echo "  $f"; done

# Append new findings to tasks.md, skipping any already present
if [[ -f "tasks.md" ]]; then
    new_findings=()
    for f in "${FINDINGS[@]}"; do
        if ! grep -qF -- "- [ ] $f" tasks.md 2>/dev/null; then
            new_findings+=("$f")
        fi
    done
    if [[ ${#new_findings[@]} -gt 0 ]]; then
        echo "" >> tasks.md
        echo "## Sweep $(date '+%Y-%m-%d %H:%M')" >> tasks.md
        for f in "${new_findings[@]}"; do
            echo "- [ ] $f" >> tasks.md
        done
        echo -e "${GREEN}Added ${#new_findings[@]} new item(s) to tasks.md${NC}"
    else
        echo -e "${GREEN}All findings already in tasks.md — nothing appended${NC}"
    fi
fi

exit 1
