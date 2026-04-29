# Delegation

## When to Delegate

This is a solo repo. Delegation is lightweight by design — invoke when the cognitive cost of local analysis exceeds the sub-agent overhead.

| Trigger (objective, measurable) | Delegate to | Gate |
|---------------------------------|-------------|------|
| Exploring a checker module not read this session | Explore agent (sonnet) | Mandatory before editing |
| Cross-module change touching ≥2 checkers | Explore agent (sonnet) | Mandatory |
| Same failure persists after 2 attempts | `codex:rescue` (sonnet) | Mandatory, blocking |
| Non-trivial plan (>3 steps, multi-file) | `codex:rescue --background --effort low` | Queue immediately after ExitPlanMode |
| Pre-merge code review | `codex:rescue` or `/review` | Recommended |

## Spawn Prompt Contract

Every sub-agent spawn must carry all four fields:

| Field | Required content |
|-------|-----------------|
| **Objective** | What output is expected (not just what to do) |
| **Output format** | How to return results (file path, stdout, structured list) |
| **Tools to use** | Which tools are in scope (Read, Grep, Glob, Bash, etc.) |
| **Boundaries** | Which files/modules to leave alone; what NOT to do |

## Effort Tiers

| Tier | Use for | Approx cost |
|------|---------|-------------|
| `low` | Plan critique, quick review, one-file diagnosis | Fast |
| `medium` | Cross-module investigation, feature diagnosis | Moderate |
| `high` | Architecture analysis, security review | High |

## Routing Table

| Task | Agent | Notes |
|------|-------|-------|
| Understand an unfamiliar checker | Explore (Explore subagent) | Pass target file + test file paths |
| Diagnose a test failure after 2 attempts | `codex:rescue` | Pass failing test output + file path |
| Review harness changes before commit | `codex:rescue` | Provide diff; ask for security + correctness review |
| Critique an implementation plan | `codex:rescue --background --effort low` | Queue immediately; check before first destructive action |
