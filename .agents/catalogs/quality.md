# Quality Catalog

## Code Quality Standards

### Linting (ruff)

#### Configuration
```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "B", "C4", "SIM"]
```

#### Rule Categories
| Category | Rules | Description |
|----------|-------|-------------|
| E | pycodestyle errors | PEP 8 style violations |
| F | pyflakes | Logical errors (unused imports, etc.) |
| I | isort | Import ordering and organization |
| B | flake8-bugbear | Common bug patterns |
| C4 | flake8-comprehensions | List/dict comprehension improvements |
| SIM | flake8-simplify | Code simplification suggestions |

#### Quality Gates
- **Zero Errors**: All ruff errors must be resolved
- **Zero Warnings**: All warnings should be addressed or explicitly ignored
- **Pre-commit**: Automatic checking before commits

### Type Checking (mypy)

#### Configuration
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
explicit_package_bases = true
namespace_packages = true
```

#### Type Coverage Standards
- **Public APIs**: 100% type annotations required
- **Internal Functions**: Strongly encouraged, not enforced
- **Return Types**: Always annotated
- **Parameter Types**: Always annotated for public functions

#### Type Annotation Patterns
```python
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd

def process_data(
    file_path: Path,
    options: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Process data from file.

    Args:
        file_path: Path to input file
        options: Optional processing options

    Returns:
        Processed DataFrame
    """
    pass
```

### Testing Standards

#### Coverage Requirements
```toml
[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

| Metric | Target | Minimum |
|--------|--------|---------|
| Line Coverage | ≥90% | ≥80% |
| Branch Coverage | ≥80% | ≥70% |
| Function Coverage | ≥95% | ≥85% |

#### Test Organization
```
tests/
  conftest.py           # Shared fixtures
  test_main.py          # Main entry point tests
  test_utils.py         # Utility function tests
  checkers/
    test_module_a.py    # Module-specific tests
    test_module_b.py
```

#### Test Naming Convention
```python
def test_<function>_<scenario>_<expected_outcome>():
    """Test that <function> <expected_outcome> when <scenario>."""
    pass

# Examples:
def test_process_data_returns_dataframe_when_valid_input():
    pass

def test_validate_path_raises_error_when_invalid_path():
    pass
```

#### Fixture Strategy
- **Scope**: Use appropriate scope (function, module, session)
- **Cleanup**: Always clean up resources
- **Isolation**: Tests must not depend on each other
- **Reusability**: Share common fixtures via conftest.py

### Documentation Standards

#### Docstring Format (Google Style)
```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief one-line description.

    Longer description if needed, explaining the function's purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2, defaults to 0

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input provided
        FileNotFoundError: When file doesn't exist

    Examples:
        >>> function_name("test", 42)
        True
    """
    pass
```

#### Documentation Requirements
- **Public Functions**: Complete docstrings with all sections
- **Private Functions**: Brief description acceptable
- **Classes**: Class docstring + method docstrings
- **Modules**: Module-level docstring explaining purpose

#### Code Comments
- **When**: Complex logic, non-obvious optimizations, workarounds
- **Style**: Complete sentences, explain WHY not WHAT
- **Language**: English only
- **Maintenance**: Update comments when code changes

### Code Review Checklist

#### Functionality
- [ ] Code meets requirements from spec
- [ ] All edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs

#### Quality
- [ ] Passes all linters (ruff)
- [ ] Passes type checker (mypy)
- [ ] Passes security scanner (bandit)
- [ ] Test coverage meets targets

#### Design
- [ ] Code is readable and maintainable
- [ ] Appropriate abstractions
- [ ] Follows existing patterns
- [ ] No unnecessary complexity

#### Documentation
- [ ] Docstrings complete and accurate
- [ ] Comments explain complex logic
- [ ] README updated if needed
- [ ] Changelog updated

#### Testing
- [ ] Tests are comprehensive
- [ ] Tests are independent
- [ ] Test names are descriptive
- [ ] Fixtures are reusable

### Continuous Integration

#### CI Pipeline Stages
1. **Lint**: ruff check
2. **Type Check**: mypy
3. **Security**: bandit
4. **Test**: pytest with coverage
5. **Build**: Package installation verification

#### Quality Gates
- All CI checks must pass before merge
- Coverage must not decrease
- No new security vulnerabilities
- No new type errors
