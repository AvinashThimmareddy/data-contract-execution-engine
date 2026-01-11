# Local Testing & Windows Deployment Guide

The engine now supports local file paths for testing before Lambda deployment, and includes Windows-specific instructions for packaging and deployment.

## Lambda Handler with Local File Support

The handler can work with both local and S3 paths. It detects S3 paths by checking for the `s3://` prefix and handles I/O appropriately.

**Supported paths**:
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

## Sample Data

The test data includes 10 customer records with some missing email values for testing completeness rules:

**Data**:
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

## Windows Deployment

On Windows, you can use PowerShell's native `Compress-Archive` cmdlet to create the deployment package without needing external tools:

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

## Updated Documentation

The QUICKSTART guide includes a new section for local testing before deployment:

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

## Lambda Event Examples

Lambda event files have been updated to use the new `source_path` and `target_path` parameters.

**Local testing example**:
```json
{
  "contract_path": "contracts/sample_contract.yaml",
  "source_path": "examples/customers_expanded.csv",
  "target_path": "output/customers_validated.csv"
}
```

## Output Directory

An `output/` directory is used for storing locally-validated data.

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

If you were using the Lambda API directly, the parameter names have changed:
- Old: `source_s3_path` → New: `source_path`
- Old: `target_s3_path` → New: `target_path`

Update Lambda test events accordingly:
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

- **Dual I/O Support**: Test locally, deploy to S3 without code changes
- **Windows-Friendly**: PowerShell `Compress-Archive` (no extra tools needed)
- **Better Documentation**: Clear examples for both local and Lambda deployments
- **Enhanced Sample Data**: 10 records with realistic edge cases

---

## Next Steps

1. **Test locally**:
   ```bash
   python -c "from runtime.lambda_handler import handler; print(handler({'contract_path': 'contracts/sample_contract.yaml', 'source_path': 'examples/customers_expanded.csv', 'target_path': 'output/customers_validated.csv'}, None))"
   ```

2. **Check the output**:
   ```bash
   cat output/customers_validated.csv
   ```

3. **Deploy to Lambda** (see LAMBDA_DEPLOYMENT.md):
   ```powershell
   Compress-Archive -Path lambda_build/* -DestinationPath lambda_function.zip -Force
   ```

4. **Test in AWS** using `lambda_event.json` with S3 paths

For more details, see [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md) and [QUICKSTART.md](QUICKSTART.md).
