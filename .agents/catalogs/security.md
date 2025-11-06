# Security Catalog

## Security Scanning

### Bandit Configuration
- **Tool**: bandit (Python security linter)
- **Scope**: All Python files in src/ and tests/
- **Exclusions**: Test files from specific security checks
- **Integration**: Pre-commit hook + CI pipeline

### Security Rules

#### High Severity
| Rule ID | Description | Action |
|---------|-------------|--------|
| B201 | Flask debug mode | Never enable in production |
| B301-B306 | Pickle usage | Avoid unless absolutely necessary |
| B303 | MD5/SHA1 usage | Use SHA256+ for cryptographic purposes |
| B308 | mark_safe usage | Sanitize all inputs |
| B501-B504 | Weak crypto | Use modern algorithms (AES-256, RSA-2048+) |
| B601-B609 | Injection risks | Parameterize all queries, validate inputs |

#### Medium Severity
| Rule ID | Description | Action |
|---------|-------------|--------|
| B101 | Assert usage | Don't use for security checks |
| B102-B112 | Dangerous functions | Review try_except_pass, exec, eval |
| B201-B202 | Flask/SQL injection | Use ORM, parameterized queries |
| B301 | Pickle | Avoid unpickling untrusted data |
| B401-B404 | Import issues | Review import security implications |

### Input Validation

#### File Paths
```python
from pathlib import Path

def validate_path(path_str: str, must_exist: bool = False) -> Path:
    """
    Validate and sanitize file paths.

    Args:
        path_str: Path string to validate
        must_exist: Whether path must exist

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid or doesn't exist when required
    """
    path = Path(path_str).resolve()

    # Prevent directory traversal
    if ".." in path.parts:
        raise ValueError(f"Invalid path: {path_str}")

    if must_exist and not path.exists():
        raise ValueError(f"Path does not exist: {path}")

    return path
```

#### Environment Variables
```python
import os
from typing import Optional

def get_env_var(key: str, required: bool = True) -> Optional[str]:
    """
    Safely retrieve environment variable.

    Args:
        key: Environment variable name
        required: Whether variable is required

    Returns:
        Environment variable value or None

    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key)

    if required and value is None:
        raise ValueError(f"Required environment variable not set: {key}")

    return value
```

### Sensitive Data Handling

#### PII (Personally Identifiable Information)
- **Never log**: Names, IDs, contact information
- **Masking**: Partial display when necessary (e.g., "김**")
- **Storage**: Encrypt at rest if persisted
- **Transmission**: TLS/HTTPS only

#### Credentials
- **Storage**: Environment variables, never in code
- **Version Control**: .env in .gitignore
- **Access**: Principle of least privilege
- **Rotation**: Regular credential rotation policy

### Dependency Security
- **Scanning**: Regular dependency vulnerability scans
- **Updates**: Timely security patch application
- **Pinning**: Lock file for reproducible builds
- **Source**: Use trusted package repositories only

### Compliance
- **Korean Personal Information Protection Act (PIPA)**
  - Purpose limitation for data collection
  - Consent for data processing
  - Secure storage and transmission
  - Access logging and audit trails
  - Data retention policies
  - Breach notification procedures
