# Quick Start Guide

Get up and running with Data Contract Execution Engine in 5 minutes!

## Prerequisites
- Python 3.7+
- pip
- AWS Account (for Lambda deployment)

## 1. Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine

# Install dependencies
pip install -r requirements.txt
```

## 2. Define Your Contract (1 minute)

Create or edit `contracts/my_contract.yaml`:

```yaml
name: "Customer Data"
version: "1.0"

source_s3_path: "s3://my-bucket/input/customers.csv"
target_s3_path: "s3://my-bucket/output/customers_validated.csv"

schema:
  columns:
    customer_id:
      type: "integer"
      nullable: false
    name:
      type: "string"
      nullable: false
    email:
      type: "string"
    age:
      type: "integer"

sla:
  min_rows: 1
  max_rows: 1000000
  completeness_threshold: 0.95
```

## 3. Test Locally (1 minute)

Run the test suite to verify everything works:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=engine --cov=runtime
```

Expected output:
```
tests/test_contract_parser.py::test_load_contract PASSED
tests/test_validation_engine.py::test_validate_schema PASSED
tests/test_sla_enforcer.py::test_enforce_sla PASSED
tests/test_pipeline_generator.py::test_generate_pipeline PASSED
tests/test_lambda_handler.py::test_handler PASSED

======================== 18+ tests passed ✅ ========================
```

Or test manually with sample data:

```bash
python -c "
import pandas as pd
from engine.contract_parser import load_contract
from engine.pipeline_generator import PipelineGenerator

# Load contract and test
contract = load_contract('contracts/sample_contract.yaml')
df = pd.read_csv('examples/customers_expanded.csv')
pipeline = PipelineGenerator(contract)
results = pipeline.generate(df)
print('✅ Validation Success!' if results.get('success') else '❌ Validation Failed')
print(results)
"
```

## 4. Test with Local Files (Before Lambda Deployment)

The engine supports **both local file paths and S3 paths**. Perfect for pre-deployment testing:

**Step 1: Create output directory**
```bash
mkdir output
```

**Step 2: Test with local paths**
```bash
python -c "
from runtime.lambda_handler import handler

# Test with local files
event = {
    'contract_path': 'contracts/sample_contract.yaml',
    'source_path': 'examples/customers_expanded.csv',
    'target_path': 'output/customers_validated.csv'
}

result = handler(event, None)
print(result)
"
```

**Step 3: Verify output**
```bash
# Check the validated data
cat output/customers_validated.csv
```

You can mix local and S3 paths:
```bash
# Read from local, write to S3
{
    "contract_path": "contracts/sample_contract.yaml",
    "source_path": "examples/customers_expanded.csv",
    "target_path": "s3://my-bucket/output/validated.csv"
}

# Read from S3, write to local
{
    "contract_path": "s3://my-bucket/contracts/contract.yaml",
    "source_path": "s3://my-bucket/data/customers.csv",
    "target_path": "output/customers_validated.csv"
}
```

## 5. Deploy to Lambda (2 minutes)

For detailed Lambda deployment instructions, see [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md).

Quick deployment:
```bash
# Create deployment package
mkdir lambda_build
cp -r engine/ lambda_build/
cp -r runtime/ lambda_build/
cp -r contracts/ lambda_build/
cp requirements.txt lambda_build/

# Create ZIP
cd lambda_build
zip -r ../lambda_function.zip .
cd ..

# Deploy (requires AWS CLI configured)
aws lambda update-function-code \
  --function-name data-contract-executor \
  --zip-file fileb://lambda_function.zip
```


## 5. Test Lambda

Create a test event:
```json
{
  "contract_path": "contracts/my_contract.yaml"
}
```

Or override paths (supports both S3 and local):
```json
{
  "contract_path": "contracts/my_contract.yaml",
  "source_path": "examples/customers_expanded.csv",
  "target_path": "output/customers_validated.csv"
}
```

The Lambda handler will:
1. Load the contract (S3 or local)
2. Read data from source path (S3 or local)
3. Validate against schema & SLA rules
4. Write to target path (S3 or local)
5. Return validation results

## Response Example

Success:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Data contract execution completed successfully",
    "contract": "Customer Data",
    "input_rows": 10,
    "output_rows": 5,
    "pipeline_results": {
      "input_rows": 5,
      "success": true,
      "steps": [...]
    }
  }
}
```

Error:
```json
{
  "statusCode": 500,
  "body": {
    "message": "Data contract execution failed: error details"
  }
}
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=engine --cov=runtime

# Run specific test
pytest tests/test_validation_engine.py -v
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Missing columns | Add columns to CSV or update contract schema |
| SLA violation | Check min_rows, max_rows, completeness_threshold |
| S3 access denied | Verify Lambda IAM role has S3 permissions |
| FileNotFoundError | Ensure contract_path is correct |

## Project Structure

```
data-contract-execution-engine/
├── engine/                  # Core modules
│   ├── contract_parser.py
│   ├── validation_engine.py
│   ├── sla_enforcer.py
│   └── pipeline_generator.py
├── runtime/
│   └── lambda_handler.py
├── contracts/
│   └── sample_contract.yaml
├── examples/
│   ├── sample_data.csv
│   └── lambda_event.json
├── tests/                   # Test suite
├── requirements.txt
├── README.md
└── QUICKSTART.md (this file)
```

## Next Steps

- Read full [README.md](README.md)
- Explore [CONTRIBUTING.md](CONTRIBUTING.md)
- Check [examples/](examples/) for more samples
- Set up tests: `pytest tests/ -v`
- Better performance on large datasets (>100MB)
- Auto-scaling
- Advanced monitoring
- ~$0.44 per DPU-hour

## Security Best Practices

1. **Use IAM Roles**: Never store AWS credentials in code
2. **S3 Encryption**: Enable encryption for sensitive data
3. **Contract Validation**: Validate contracts before deployment
4. **Logging**: Review CloudWatch logs for security issues
5. **Least Privilege**: Grant minimum required permissions

## Performance Tips

### For Lambda (< 100MB data)
- ✅ Keep memory at 3GB minimum
- ✅ Use CSV format
- ✅ Simple transformations
- ✅ Set timeout to 15 minutes

### For Glue (> 100MB data)
- ✅ Use Parquet format
- ✅ Parallel processing
- ✅ Auto-scaling workers
- ✅ Better for batch jobs

---

**Happy data processing!** 🚀

Questions? See our documentation or open an issue on GitHub.
