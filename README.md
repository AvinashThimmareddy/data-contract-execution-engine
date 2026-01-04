# Data Contract Execution Engine

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Overview

**Data Contract Execution Engine (DCEE)** is a lightweight Python framework for validating data against contracts and enforcing SLA rules. Built on pandas and boto3, it provides simple, fast data validation without heavy dependencies.

It reads YAML contract definitions that specify:
- **Schema requirements** (column names, types, nullability)
- **SLA rules** (min/max rows, data completeness)
- **Source and target S3 paths** for data files

The engine validates data on ingestion to ensure quality and consistency before writing to target destinations. Deploy as a Lambda function for serverless validation pipelines.

---

## Key Features

- **Simple Python implementation** - No heavy dependencies, easy to understand
- **YAML-based contracts** - Define schemas and SLA rules declaratively
- **Data quality validation** - Schema, constraints, and SLA checks
- **AWS Lambda ready** - Deploy as a Lambda function for serverless validation
- **S3 integration** - Read from and write to S3 effortlessly
- **Pandas-based processing** - Uses pandas for lightweight data manipulation

---

## Current Limitations

- **CSV files only** - Currently supports CSV format only
  - No support for TXT files with custom delimiters (tab, pipe, space, etc.)
  - No support for other formats (JSON, Parquet, Excel, etc.)
  - **Workaround**: See [CONTRIBUTING.md](CONTRIBUTING.md) for implementing multi-format support

- **Single-machine processing** - Best for datasets < 1GB
  - Loads entire dataset into memory
  - Not suitable for very large files (use Spark for distributed processing)

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start

Get started in 5 minutes! See [QUICKSTART.md](QUICKSTART.md) for detailed instructions including:
- Local testing with sample data
- Testing with local file paths
- Deploying to AWS Lambda
- Running tests with coverage

Quick example:

### 1. Create a Contract

Define a YAML contract file (`contracts/sample_contract.yaml`):

```yaml
name: "Customer Data Contract"
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
      nullable: true

sla:
  min_rows: 1
  max_rows: 1000000
  completeness_threshold: 0.95
```

### 2. Run Locally

```python
from engine.contract_parser import load_contract
from engine.pipeline_generator import PipelineGenerator
import pandas as pd

# Load contract
contract = load_contract("contracts/sample_contract.yaml")

# Read data
df = pd.read_csv("sample_data.csv")

# Validate
pipeline = PipelineGenerator(contract)
results = pipeline.generate(df)

print(f"Validation passed: {results['success']}")
```

### 3. Deploy to AWS Lambda

See [LAMBDA_DEPLOYMENT.md](LAMBDA_DEPLOYMENT.md) for complete step-by-step deployment instructions.

---

## Project Structure

```
├── engine/
│   ├── __init__.py
│   ├── contract_parser.py      # Load and parse YAML contracts
│   ├── validation_engine.py     # Schema and data quality validation
│   ├── sla_enforcer.py          # SLA rule enforcement
│   └── pipeline_generator.py    # Orchestrate validation pipeline
├── runtime/
│   └── lambda_handler.py        # AWS Lambda entry point
├── contracts/
│   └── sample_contract.yaml     # Example contract
├── tests/
│   └── ...                      # Unit tests
├── requirements.txt
└── README.md
```

---

## Dependencies

- **pandas** - Data manipulation
- **pyyaml** - Contract parsing
- **boto3** - AWS S3 access
- **pytest** - Testing framework

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and coding standards
- How to implement new features
- Testing requirements
- Planned enhancements (multi-format file support, custom transformations, etc.)

Quick steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -am 'Add my feature'`)
4. Push to branch (`git push origin feature/my-feature`)
5. Create a Pull Request

---

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) file for details.
