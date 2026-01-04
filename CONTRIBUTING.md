# Development Guide for Contributors

## Project Overview

The Data Contract Execution Engine (DCEE) is a lightweight Python framework that:
1. **Parses** data contracts (YAML format)
2. **Validates** incoming data against schema and constraints
3. **Enforces** Service Level Agreements (SLAs)
4. **Processes** data with pandas
5. **Runs** on AWS Lambda for serverless validation

## Architecture

```
Contract (YAML)
    ↓
ContractParser
    ↓
PipelineGenerator
    ├─ ValidationEngine (schema, constraints, quality)
    └─ SLAEnforcer (row counts, completeness)
    ↓
Output (CSV)
```

## Module Responsibilities

### `engine/contract_parser.py`
- **Purpose:** Load and parse data contracts
- **Key Functions:**
  - `load_contract()`: Loads YAML contract from S3 or local file
- **Extending:** Add new contract formats (if needed)

### `engine/validation_engine.py`
- **Purpose:** Runtime validation of data
- **Key Methods:**
  - `validate_schema()`: Check column existence and types
  - `validate_data_quality()`: Measure nulls, duplicates
  - `validate_constraints()`: Check custom constraints
- **Extending:** Add new constraint types (regex, range, enum)

### `engine/sla_enforcer.py`
- **Purpose:** Monitor and enforce SLAs
- **Key Methods:**
  - `enforce_sla()`: Check SLA rules against data
  - `get_metrics()`: Get compliance metrics
- **Extending:** Add new SLA rules (custom thresholds, patterns)

### `engine/pipeline_generator.py`
- **Purpose:** Orchestrate the entire pipeline
- **Key Methods:**
  - `generate()`: Execute full validation pipeline
- **Extending:** Add new validation types

### `runtime/lambda_handler.py`
- **Purpose:** AWS Lambda entry point
- **Features:** S3 integration via boto3

## Adding New Features

### 1. New Validation Type

**File:** `engine/validation_engine.py`

```python
def validate_custom(self, df: pd.DataFrame) -> dict:
    """Add custom validation logic"""
    errors = []
    
    # Add your validation logic
    for col in df.columns:
        # Example: check for custom pattern
        pass
    
    return {"status": "passed" if not errors else "failed", "errors": errors}
```

**Contract Usage:**
```yaml
schema:
  columns:
    email:
      type: "string"
      nullable: false
```

### 2. New Constraint Type

**File:** `engine/validation_engine.py`

```python
def validate_constraints(self, df: DataFrame, constraints: List[Dict]) -> bool:
    for constraint in constraints:
        constraint_type = constraint.get("type")
        
        # Add here:
        elif constraint_type == "regex":
            column = constraint.get("column")
            pattern = constraint.get("pattern")
def validate_pattern(self, df: pd.DataFrame, column: str, pattern: str) -> bool:
    """Validate column matches pattern"""
    invalid_count = df[~df[column].astype(str).str.match(pattern)].shape[0]
    if invalid_count > 0:
        print(f"Constraint violation: {invalid_count} rows don't match pattern")
        return False
    return True

def validate_enum(self, df: pd.DataFrame, column: str, allowed_values: list) -> bool:
    """Validate column values are in allowed set"""
    invalid_count = df[~df[column].isin(allowed_values)].shape[0]
    if invalid_count > 0:
        return False
    return True
```

**Contract Usage:**
```yaml
schema:
  columns:
    email:
      type: "string"
      pattern: "^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
    country:
      type: "string"
      enum: ["US", "CA", "MX"]
```

### 3. New SLA Rule

**File:** `engine/sla_enforcer.py`

```python
def enforce_sla(self, df: pd.DataFrame) -> dict:
    """Enforce SLA rules against data"""
    results = {
        "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        "sla_passed": True,
        "violations": [],
        "metrics": {}
    }
    
    # Add custom SLA checks here
    sla_rules = self.contract.get("sla", {})
    
    if "custom_threshold" in sla_rules:
        threshold = sla_rules["custom_threshold"]
        # Add your custom logic
        pass
    
    return results
```

### 4. Support Multiple File Formats (TXT, TSV, Delimiter-Separated)

**Current Limitation**: Engine only reads/writes CSV files.

**Enhancement**: Add support for TXT files with custom delimiters (tab, pipe, space, custom)

**File:** `runtime/lambda_handler.py`

```python
def _read_delimited_file_from_s3(s3_path: str, delimiter: str = ",") -> pd.DataFrame:
    """Read delimited file from S3 path with custom delimiter."""
    bucket, key = s3_path.replace("s3://", "").split("/", 1)
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj["Body"], delimiter=delimiter)
    return df


def _write_delimited_file_to_s3(df: pd.DataFrame, s3_path: str, delimiter: str = ",") -> None:
    """Write delimited file to S3 path with custom delimiter."""
    bucket, key = s3_path.replace("s3://", "").split("/", 1)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=delimiter)
    s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())
```

**Contract Extension**:
```yaml
name: "Customer Data"
version: "1.0"

source_s3_path: "s3://my-bucket/input/customers.txt"
source_delimiter: "\t"  # Tab-separated

target_s3_path: "s3://my-bucket/output/validated.csv"
target_delimiter: ","   # Comma-separated (default)

schema:
  columns:
    customer_id:
      type: "integer"
    name:
      type: "string"
```

**Update Lambda Handler**:
```python
# Get delimiters from contract
source_delimiter = contract.get("source_delimiter", ",")
target_delimiter = contract.get("target_delimiter", ",")

# Read with custom delimiter
df = _read_delimited_file_from_s3(source_path, source_delimiter)

# Write with custom delimiter
_write_delimited_file_to_s3(df, target_path, target_delimiter)
```

**Supported Delimiters**:
- `","` - Comma (CSV) - default
- `"\t"` - Tab (TSV)
- `"|"` - Pipe
- `" "` - Space
- `":"` or any custom character

## Testing Strategy

### Local Testing (Python Unit Tests)
```bash
pytest tests/test_contract_parser.py -v
pytest tests/test_validation_engine.py -v
pytest tests/test_sla_enforcer.py -v
pytest tests/test_pipeline_generator.py -v
```

### Lambda Testing (AWS Environment)
1. Deploy using `LAMBDA_DEPLOYMENT.md`
2. Invoke with test data
3. Monitor CloudWatch logs
4. Verify S3 output

## Code Standards

### Style
- Follow PEP 8
- Use type hints for all functions
- Document with docstrings
- Keep functions focused and small

### Example:
```python
def validate_schema(self, df: pd.DataFrame) -> bool:
    """
    Validate dataframe schema against contract schema.
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        True if schema is valid, False otherwise
    """
    # Implementation
    pass
```

### Testing
- Write unit tests for new functionality
- Test with both valid and invalid inputs
- Mock external dependencies (S3, databases)

## Common Tasks

### Debug Pipeline Issues
```python
# Add temporary logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"DataFrame shape: {df.shape}")
logger.info(f"Row count: {len(df)}")
logger.info(f"Sample data:\n{df.head()}")
```

### Profile Performance
```python
import time
start = time.time()
results = pipeline.generate(df)
duration = time.time() - start
print(f"Validation took {duration:.2f} seconds")
```

### Handle Large Files
```python
# Use pandas chunking for large CSVs
chunk_size = 100000
for chunk in pd.read_csv("data.csv", chunksize=chunk_size):
    results = pipeline.generate(chunk)
    # Process results
```

## Deployment Checklist

- [ ] Code follows PEP 8 style guide
- [ ] All functions have type hints
- [ ] Unit tests written and passing
- [ ] Lambda deployment tested
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] No hardcoded credentials or secrets
- [ ] Error handling implemented
- [ ] Logging statements added
- [ ] Performance optimized for Lambda constraints

## Resources

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/limits.html)
- [Data Contracts in Data Mesh](https://www.datamesh-learning.com/)

## Getting Help

- Check existing issues on GitHub
- Review examples in `examples/` folder
- Read docstrings in code
- Check CloudWatch logs for errors
- Ask in GitHub Discussions

Happy coding! 🚀
