# Data Pipeline Pattern

## Overview
Common patterns for data processing pipelines in Python CLI tools.

## Architecture

### Pipeline Stages
```
INPUT → EXTRACT → TRANSFORM → DETECT → OUTPUT
```

1. **INPUT**: File discovery and loading
2. **EXTRACT**: Parse and load data into memory
3. **TRANSFORM**: Clean, filter, enrich data
4. **DETECT**: Apply business logic and rules
5. **OUTPUT**: Generate reports and summaries

## Implementation Patterns

### 1. Checker Pattern
Each data processing module follows a consistent interface:

```python
from pathlib import Path
import pandas as pd

def run_check(
    download_dir: Path,
    save_dir: Path,
    reference_date: datetime
) -> int:
    """
    Execute data check and generate report.

    Args:
        download_dir: Directory containing input files
        save_dir: Directory for output reports
        reference_date: Reference date for processing

    Returns:
        Number of records processed

    Raises:
        FileNotFoundError: When input files missing
        ValueError: When invalid data format
    """
    # 1. Load data
    df = load_data(download_dir)

    # 2. Validate schema
    validate_schema(df)

    # 3. Transform data
    df_clean = transform_data(df, reference_date)

    # 4. Apply detection logic
    results = detect_anomalies(df_clean)

    # 5. Generate report
    if not results.empty:
        save_report(results, save_dir)

    return len(df)
```

### 2. Orchestration Pattern
Main orchestrator coordinates multiple checkers:

```python
def main() -> None:
    """Main orchestration function."""
    # Setup
    config = load_config()
    checkers = discover_checkers()

    # Execute pipeline
    total_count = 0
    for checker in checkers:
        try:
            count = checker.run_check(
                config.download_dir,
                config.save_dir,
                config.reference_date
            )
            total_count += count
        except Exception as e:
            handle_error(checker.name, e)

    # Summary
    print_summary(total_count)
```

### 3. Data Loading Pattern
Consistent data loading with error handling:

```python
def load_excel_files(
    directory: Path,
    prefix: str,
    required_columns: List[str]
) -> pd.DataFrame:
    """
    Load and concatenate Excel files.

    Args:
        directory: Directory containing files
        prefix: Filename prefix filter
        required_columns: Required column names

    Returns:
        Concatenated DataFrame

    Raises:
        FileNotFoundError: When no matching files found
        ValueError: When schema validation fails
    """
    files = list(directory.glob(f"{prefix}*.xls*"))

    if not files:
        raise FileNotFoundError(
            f"No files with prefix '{prefix}' in {directory}"
        )

    dfs = []
    for file in files:
        try:
            df = pd.read_excel(file)
            validate_columns(df, required_columns)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Skipping {file.name}: {e}")

    return pd.concat(dfs, ignore_index=True)
```

### 4. Validation Pattern
Multi-level validation:

```python
def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate DataFrame schema.

    Args:
        df: DataFrame to validate

    Raises:
        ValueError: When validation fails
    """
    required = {'사용자ID', '접속일시', '작업구분'}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Empty DataFrame")
```

### 5. Transformation Pattern
Data cleaning and enrichment:

```python
def transform_data(
    df: pd.DataFrame,
    reference_date: datetime
) -> pd.DataFrame:
    """
    Clean and transform raw data.

    Args:
        df: Raw DataFrame
        reference_date: Reference date for calculations

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # 1. Type conversion
    df['접속일시'] = pd.to_datetime(df['접속일시'])

    # 2. Data cleaning
    df = df.dropna(subset=['사용자ID'])
    df['사용자ID'] = df['사용자ID'].str.strip()

    # 3. Derived columns
    df['date'] = df['접속일시'].dt.date
    df['is_business_hours'] = df['접속일시'].apply(
        lambda x: 9 <= x.hour < 18
    )

    # 4. Filtering
    df = df[df['date'] >= reference_date.date()]

    return df
```

### 6. Detection Pattern
Apply business rules:

```python
def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect anomalies based on business rules.

    Args:
        df: Clean DataFrame

    Returns:
        DataFrame containing detected anomalies
    """
    anomalies = []

    # Rule 1: Bulk queries
    user_counts = df.groupby('사용자ID').size()
    bulk_users = user_counts[user_counts > BULK_THRESHOLD]

    for user_id in bulk_users.index:
        anomalies.append({
            'user_id': user_id,
            'anomaly_type': 'BULK_QUERY',
            'count': bulk_users[user_id],
            'severity': 'HIGH'
        })

    # Rule 2: Off-hours access
    off_hours = df[~df['is_business_hours']]
    for _, row in off_hours.iterrows():
        anomalies.append({
            'user_id': row['사용자ID'],
            'anomaly_type': 'OFF_HOURS',
            'timestamp': row['접속일시'],
            'severity': 'MEDIUM'
        })

    return pd.DataFrame(anomalies)
```

### 7. Output Pattern
Standardized report generation:

```python
def save_report(
    results: pd.DataFrame,
    save_dir: Path,
    report_name: str
) -> None:
    """
    Save detection results to Excel.

    Args:
        results: Detection results DataFrame
        save_dir: Output directory
        report_name: Report filename
    """
    save_dir.mkdir(parents=True, exist_ok=True)

    output_path = save_dir / f"{report_name}_{datetime.now():%Y%m%d}.xlsx"

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary sheet
        summary = generate_summary(results)
        summary.to_excel(writer, sheet_name='Summary', index=False)

        # Detail sheet
        results.to_excel(writer, sheet_name='Details', index=False)

    logger.info(f"Report saved: {output_path}")
```

## Error Handling Strategy

### Recovery Patterns
```python
def resilient_checker(func):
    """Decorator for resilient checker execution."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"Input file missing: {e}")
            return 0  # Return zero count, continue
        except ValueError as e:
            logger.error(f"Data validation failed: {e}")
            return 0
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise  # Re-raise unexpected errors
    return wrapper
```

## Performance Optimization

### Memory Management
- Use chunking for large files: `pd.read_excel(chunksize=10000)`
- Filter early to reduce data size
- Use appropriate dtypes: `df.astype({'col': 'category'})`
- Clean up large objects: `del df; gc.collect()`

### I/O Optimization
- Batch file operations
- Use context managers for file handles
- Parallel processing for independent checkers

## Testing Strategy

### Test Data Fixtures
```python
@pytest.fixture
def sample_access_log():
    """Sample access log for testing."""
    return pd.DataFrame({
        '사용자ID': ['user1', 'user2'],
        '접속일시': [datetime(2025, 1, 1), datetime(2025, 1, 2)],
        '작업구분': ['조회', '다운로드']
    })
```

### Integration Tests
- Test full pipeline with realistic data
- Verify report generation
- Check error handling paths
