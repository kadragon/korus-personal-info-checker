# Error Catalog

## Error Categories

### Configuration Errors
| Error ID | Description | Handling |
|----------|-------------|----------|
| CFG-001 | Missing .env file | Exit with clear message and .env.example reference |
| CFG-002 | Invalid environment variable | Exit with validation error and expected format |
| CFG-003 | Missing required environment variable | Exit with list of required variables |

### File System Errors
| Error ID | Description | Handling |
|----------|-------------|----------|
| FS-001 | Directory not found | Exit with path validation error |
| FS-002 | File not found | Skip and log warning, continue processing |
| FS-003 | Permission denied | Exit with permission error and suggested fix |
| FS-004 | Disk space exhausted | Exit with space check error |

### Data Processing Errors
| Error ID | Description | Handling |
|----------|-------------|----------|
| DATA-001 | Excel file corrupted | Skip file, log error, continue |
| DATA-002 | Unexpected column schema | Log warning, attempt graceful handling |
| DATA-003 | Invalid data type | Coerce or skip row, log warning |
| DATA-004 | Empty dataset | Log info, skip processing |

### Runtime Errors
| Error ID | Description | Handling |
|----------|-------------|----------|
| RT-001 | Out of memory | Exit with memory error and data size info |
| RT-002 | Timeout | Log timeout, attempt retry or skip |
| RT-003 | External dependency failure | Exit with dependency error |

## Error Response Template

```python
from rich.console import Console

console = Console()

def handle_error(error_id: str, detail: str, suggestion: str = "") -> None:
    """
    Standardized error handler.

    Args:
        error_id: Error catalog ID
        detail: Specific error detail
        suggestion: Optional recovery suggestion
    """
    console.print(f"[bold red]Error {error_id}:[/bold red] {detail}")
    if suggestion:
        console.print(f"[yellow]Suggestion:[/yellow] {suggestion}")
```

## Exit Codes
- `0`: Success
- `1`: Configuration error
- `2`: File system error
- `3`: Data processing error
- `4`: Runtime error
- `5`: Unexpected error

## Logging Strategy
- **Error**: Critical failures requiring user intervention
- **Warning**: Non-fatal issues that may affect results
- **Info**: Progress and completion messages
- **Debug**: Detailed diagnostic information (dev mode only)
