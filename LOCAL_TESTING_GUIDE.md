# Local Testing & Windows Deployment Guide

## Summary of Changes

This update enables the Data Contract Execution Engine to support **local file paths** for testing before Lambda deployment, and provides **Windows-specific deployment instructions**.

## 1. ✅ Enhanced Lambda Handler with Local File Support

**File**: `runtime/lambda_handler.py`

**Key Changes**:
- Added `_is_s3_path()` helper to detect S3 vs local paths
- Added `_read_csv()` function that handles both S3 and local CSV files
- Added `_write_csv()` function that handles both S3 and local CSV files
- Auto-creates output directories for local paths
- Updated handler docstring with examples for both S3 and local testing
- Changed parameter names from `source_s3_path`/`target_s3_path` to `source_path`/`target_path` (more generic)

**Now Supports**:
```python
# S3 paths (Lambda deployment)
{
    "contract_path": "s3://bucket/contracts/contract.yaml",
    "source_path": "s3://bucket/data/customers.csv",
    "target_path": "s3://bucket/output/validated.csv"
}

# Local paths (local testing)
{
    "contract_path": "contracts/sample_contract.yaml",
    "source_path": "examples/customers_expanded.csv",
    "target_path": "output/customers_validated.csv"
}

# Mixed paths (flexible)
{
    "contract_path": "contracts/sample_contract.yaml",
    "source_path": "s3://bucket/data/customers.csv",
    "target_path": "output/validated.csv"
}
```

## 2. ✅ Enhanced Sample Data

**File**: `examples/customers_expanded.csv` (NEW)

**Details**:
- 10 customer records (expanded from 5)
- Includes missing values for testing completeness SLA rules
- Covers various ages for data diversity
- Ready for local testing

**Records**:
```
customer_id,name,email,age
C001,John Smith,john.smith@company.com,32
C002,Sarah Johnson,sarah.johnson@company.com,28
C003,Michael Chen,michael.chen@company.com,45
C004,Emma Williams,,35           <- missing email
C005,Robert Martinez,robert.martinez@company.com,52
C006,Lisa Anderson,,29           <- missing email
C007,David Brown,david.brown@company.com,41
C008,Jessica Garcia,jessica.garcia@company.com,38
C009,James Wilson,,50            <- missing email
C010,Amanda Taylor,amanda.taylor@company.com,26
```

## 3. ✅ Windows Deployment Instructions

**File**: `LAMBDA_DEPLOYMENT.md`

**Windows Users**: Use PowerShell's native `Compress-Archive` (no installation needed):

```powershell
# Create deployment package
mkdir lambda_build
Copy-Item -Path engine -Destination lambda_build -Recurse
Copy-Item -Path runtime -Destination lambda_build -Recurse
Copy-Item -Path contracts -Destination lambda_build -Recurse
Copy-Item -Path requirements.txt -Destination lambda_build

# Create ZIP (native PowerShell, no zip command needed!)
Compress-Archive -Path lambda_build/* -DestinationPath lambda_function.zip -Force
```

## 4. ✅ Updated QUICKSTART.md with Local Testing Workflow

**File**: `QUICKSTART.md`

**New Section**: "Test with Local Files (Before Lambda Deployment)"

**Workflow**:
1. Create output directory: `mkdir output`
2. Run validation with local paths
3. Verify output: `cat output/customers_validated.csv`
4. Deploy to Lambda

**Example**:
```bash
python -c "
from runtime.lambda_handler import handler

event = {
    'contract_path': 'contracts/sample_contract.yaml',
    'source_path': 'examples/customers_expanded.csv',
    'target_path': 'output/customers_validated.csv'
}

result = handler(event, None)
print(result)
"
```

## 5. ✅ Updated Lambda Event Examples

**Files Modified**:
- `examples/lambda_event.json` - Updated to use `source_path`/`target_path`
- `examples/lambda_event_local.json` (NEW) - Local testing example

**Local Testing Example**:
```json
{
  "contract_path": "contracts/sample_contract.yaml",
  "source_path": "examples/customers_expanded.csv",
  "target_path": "output/customers_validated.csv"
}
```

## 6. ✅ Output Directory

**Directory Created**: `output/` 
- For storing locally-validated data
- Added to .gitignore (recommended)

---

## Testing the Changes Locally

### Scenario 1: Test with Local Files
```bash
# All files local
python -c "
from runtime.lambda_handler import handler

event = {
    'contract_path': 'contracts/sample_contract.yaml',
    'source_path': 'examples/customers_expanded.csv',
    'target_path': 'output/customers_validated.csv'
}

result = handler(event, None)
print('Status:', result['statusCode'])
print('Message:', result['body'])
"
```

### Scenario 2: Test Contract Only (No S3 Needed)
```bash
python -c "
from engine.contract_parser import load_contract

contract = load_contract('contracts/sample_contract.yaml')
print(f'Contract: {contract.name} v{contract.version}')
print(f'Columns: {list(contract.schema.columns.keys())}')
"
```

### Scenario 3: Data Quality Testing
The expanded sample data includes:
- **Missing emails** (C004, C006, C009) - Tests completeness_threshold SLA
- **10 records** - Tests min_rows/max_rows SLA
- **Age variety** - Tests schema validation for numeric types

Expected completeness: 8/10 * 100 = 80% (less than 95% threshold if set)

---

## Breaking Changes

⚠️ **Parameter Names Changed** (If using Lambda API directly):
- Old: `source_s3_path` → New: `source_path`
- Old: `target_s3_path` → New: `target_path`

Update Lambda test events:
```json
// OLD (no longer works)
{
  "contract_path": "...",
  "source_s3_path": "s3://...",
  "target_s3_path": "s3://..."
}

// NEW (supports S3 and local)
{
  "contract_path": "...",
  "source_path": "s3://...",
  "target_path": "s3://..."
}
```

---

## Key Benefits

✅ **Dual I/O Support**: Test locally, deploy to S3 without code changes
✅ **Windows-Friendly**: PowerShell `Compress-Archive` (no extra tools needed)
✅ **Better Documentation**: Clear examples for both local and Lambda deployments
✅ **Enhanced Sample Data**: 10 records with realistic edge cases
✅ **Backward Compatible**: Lambda still works the same way, just more flexible paths

---

## Next Steps

1. **Test Locally**:
   ```bash
   python -c "from runtime.lambda_handler import handler; print(handler({'contract_path': 'contracts/sample_contract.yaml', 'source_path': 'examples/customers_expanded.csv', 'target_path': 'output/customers_validated.csv'}, None))"
   ```

2. **Verify Output**:
   ```bash
   cat output/customers_validated.csv
   ```

3. **Deploy to Lambda** (see LAMBDA_DEPLOYMENT.md):
   ```powershell
   Compress-Archive -Path lambda_build/* -DestinationPath lambda_function.zip -Force
   ```

4. **Test in AWS** using the updated `lambda_event.json` with S3 paths

---

**Documentation**: See [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md) and [QUICKSTART.md](QUICKSTART.md) for complete deployment instructions.
