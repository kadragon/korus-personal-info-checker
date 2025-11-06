# KORUS Personal Info Checker - Agent Constitution

**Last Updated**: 2025-11-06
**Framework**: SDD×TDD (Spec-Driven Development × Test-Driven Development)

## Overview

This project follows the SDD×TDD framework with a hierarchical organization system separating concerns across three core directories:

- **`.agents/`** - Organizational constitution (HOW we build)
- **`.spec/`** - Specification SSOT (WHAT we build)
- **`.tasks/`** - Operational execution (WHEN/WHO/WHY)

## Directory Structure

```
.agents/
  profiles/           # Development profiles
    python-cli.md                 # Base Python CLI profile
    python-cli@2025-11-06.md      # Project-specific version
  catalogs/           # Standards and conventions
    errors.md                     # Error handling
    quality.md                    # Code quality
    security.md                   # Security standards
  patterns/           # Architecture patterns
    data-pipeline.md              # Data processing patterns
  memory/
    index.md          # Active specs/tasks summary (≤200 lines)
  OWNERS              # Maintainer information
  README.md           # Project quick reference
  AGENTS.md           # This file - navigation guide

.spec/
  feature/
    */spec.md         # Feature specifications with front-matter

.tasks/
  backlog.md          # Pending tasks
  log-YYYY-MM-DD.md   # Daily development logs
  task-*.md           # Individual task records
  _archive/           # Historical task archive
```

## Profiles

### python-cli.md
**Path**: `profiles/python-cli.md`
**Purpose**: Base profile for Python CLI tools
**Contents**:
- Core principles and conventions
- Technology stack standards
- Architecture patterns
- Quality and documentation standards

### python-cli@2025-11-06.md
**Path**: `profiles/python-cli@2025-11-06.md`
**Version**: 2025-11-06
**Base**: `profiles/python-cli.md`

**Purpose**: Project-specific configuration and context
**Contents**:
- Project overview and domain context (KORUS Personal Info Checker)
- Architecture and data flow
- Configuration (environment variables, schemas)
- Quality targets (99% coverage achieved)
- Security considerations (PIPA compliance)
- Applied catalogs and patterns
- Change history

## Catalogs

### errors.md
**Path**: `catalogs/errors.md`
**Purpose**: Error handling standards
**Contents**:
- Error categories and codes
- Error response templates
- Exit codes
- Logging strategy

### security.md
**Path**: `catalogs/security.md`
**Purpose**: Security standards and compliance
**Contents**:
- Bandit configuration
- Security rules (by severity)
- Input validation patterns
- PII handling (PIPA compliance)
- Dependency security

### quality.md
**Path**: `catalogs/quality.md`
**Purpose**: Code quality standards
**Contents**:
- Linting rules (ruff)
- Type checking standards (mypy)
- Testing requirements (coverage targets)
- Documentation standards
- Code review checklist

## Patterns

### data-pipeline.md
**Path**: `patterns/data-pipeline.md`
**Purpose**: Data processing pipeline patterns
**Contents**:
- Pipeline stages (INPUT → EXTRACT → TRANSFORM → DETECT → OUTPUT)
- Checker pattern
- Orchestration pattern
- Validation, transformation, detection patterns
- Error handling and performance optimization

## Memory Index

**Path**: `memory/index.md`
**Purpose**: Active specs and tasks summary
**Update Frequency**: On spec/task status changes
**Contents**:
- Active specifications (with traces)
- Archived specifications (summary)
- Active and historical tasks
- Profile and catalog usage
- Quality metrics
- Project health indicators

**Size Limit**: ≤200 lines

## How to Use This System

### For Development
1. Check `memory/index.md` for active specs and tasks
2. Reference relevant catalog for standards (errors, security, quality)
3. Follow patterns from `patterns/data-pipeline.md`
4. Ensure changes trace back to SPEC-ID

### For New Features
1. Create spec in `.spec/feature/`
2. Add front-matter referencing agents profiles and catalogs
3. Create task in `.tasks/` linked to SPEC-ID
4. Follow TDD: RED → GREEN → REFACTOR
5. Update `memory/index.md` when spec status changes

### For Quality Gates
All changes must pass:
- **Lint**: `ruff check src/` (0 issues)
- **Type Check**: `mypy src/` (0 errors)
- **Security**: `bandit -r src/` (0 vulnerabilities)
- **Tests**: `pytest --cov=src` (≥80% coverage, all tests pass)

### For Documentation
- **Code**: English docstrings (Google style)
- **Specs**: `.spec/feature/*/spec.md` with GWT format
- **Tasks**: `.tasks/task-*.md` with DoD checklist
- **Profiles**: `.agents/` for reusable standards

## Constitutional Principles

1. **Spec is SSOT** - Every change traces to `.spec/`
2. **TDD First** - RED → GREEN → REFACTOR cycle
3. **Profiles Govern** - `.agents/` define NFR and constraints
4. **Trace Required** - Each commit/test/file references SPEC-ID, TEST-ID
5. **No Over-generation** - Minimum artifacts needed
6. **Ambiguity = Halt** - Stop if spec unclear, log in `.tasks/backlog.md`
7. **Memory Hygiene** - Keep `memory/index.md` ≤200 lines
8. **Rollback on Failure** - Shrink scope, log cause in `.tasks/log-*.md`

## Separation of Concerns

| Directory | Function | Persistence |
|-----------|----------|-------------|
| `.agents/` | How we build (organizational truth) | Stable, versioned |
| `.spec/` | What we build (functional truth) | Volatile |
| `.tasks/` | When/Who/Why (execution truth) | Historical ledger |

## Quality Gates Enforcement

```yaml
quality_gates:
  coverage: { lines: 80, branches: 70 }
  current: { lines: 99, branches: 80 }  # Exceeds targets
  perf_regression: none
  security_scan: must_pass
  lint: must_pass
  type_check: must_pass
```

## Migration History

### 2025-11-06: SDD×TDD Framework Migration
- Restructured `.agents/` from single file to hierarchical system
- Created global profiles, catalogs, and patterns
- Established project-specific profile with versioning
- Added front-matter to all `.spec/` files
- Created `.tasks/backlog.md` and `.tasks/log-*.md` structure
- Generated `.agents/memory/index.md` for active tracking
- Backed up original AGENTS.md to AGENTS.md.backup

### Pre-2025-11-06
See `AGENTS.md.backup` for original flat structure and changelog.

## References

### Quick Links
- **Project README**: `README.md`
- **Current Profile**: `profiles/python-cli@2025-11-06.md`
- **Active Specs**: `memory/index.md`
- **Backlog**: `.tasks/backlog.md`
- **Latest Log**: `.tasks/log-2025-11-06.md`

### External Documentation

- **SDD×TDD Framework** - See global system prompt for framework details
- [Python CLI Profile](profiles/python-cli.md) - Base standards
- [Data Pipeline Pattern](patterns/data-pipeline.md) - Architecture patterns

---

**For questions or updates**: See `OWNERS`
