# AWS Lambda Deployment Guide

Simple guide to deploy the Data Contract Execution Engine to AWS Lambda.

## Prerequisites

- AWS Account with Lambda and S3 permissions
- AWS CLI configured: `aws configure`
- Python 3.7+
- Git

## Quick Start

### 1. Create Deployment Package

**On Windows (PowerShell):**
```powershell
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine

Remove-Item lambda_build -Recurse -Force -ErrorAction SilentlyContinue
mkdir lambda_build

Copy-Item -Path engine -Destination lambda_build -Recurse
Copy-Item -Path runtime -Destination lambda_build -Recurse
Copy-Item -Path contracts -Destination lambda_build -Recurse

pip install PyYAML -t lambda_build

Compress-Archive -Path lambda_build/* -DestinationPath lambda_function.zip -Force

$size = (Get-Item lambda_function.zip).Length / 1MB
Write-Host "Package size: $size MB"
```

**On Mac/Linux:**
```bash
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine

mkdir lambda_build
cp -r engine/ lambda_build/
cp -r runtime/ lambda_build/
cp -r contracts/ lambda_build/

pip install PyYAML -t lambda_build

cd lambda_build
zip -r ../lambda_function.zip .
cd ..
```

The deployment package includes PyYAML for parsing contracts. Other dependencies like pandas and boto3 come from a Lambda Layer.

### 2. Add Lambda Layer (AWSSDKPandas-Python311)

The AWSSDKPandas layer provides pandas, boto3, and other dependencies. This keeps the deployment package small.

**Via AWS Console:**

1. Go to [Lambda Console](https://console.aws.amazon.com/lambda/home#/functions)
2. Click your function: `data-contract-executor`
3. Scroll to **Layers** section
4. Click **Add a layer**
5. Choose **AWS Layers**
6. Search for: `AWSSDKPandas-python311`
7. Select it and click **Add**

**Via AWS CLI:**
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --layers arn:aws:lambda:us-east-1:${ACCOUNT_ID}:layer:AWSSDKPandas-Python311
```

### 3. Create IAM Role

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name DataContractExecutorRole \
  --assume-role-policy-document file://trust-policy.json

# Create S3 access policy
cat > s3-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::*/*"
  }]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name DataContractExecutorRole \
  --policy-name DataContractS3Access \
  --policy-document file://s3-policy.json

# Attach basic Lambda execution role
aws iam attach-role-policy \
  --role-name DataContractExecutorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### 4. Create Lambda Function

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws lambda create-function \
  --function-name data-contract-executor \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/DataContractExecutorRole \
  --handler runtime.lambda_handler.handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30 \
  --memory-size 256 \
  --description "Data Contract Execution Engine"
```

### 5. Test the Function

Create a test event:
```json
{
  "contract_path": "contracts/sample_contract.yaml",
  "source_path": "s3://my-bucket/input/data.csv",
  "target_path": "s3://my-bucket/output/data_validated.csv"
}
```

Test via CLI:
```bash
aws lambda invoke \
  --function-name data-contract-executor \
  --payload file://test_event.json \
  response.json

cat response.json
```

## Function Input

The function accepts this input format:
```json
{
  "contract_path": "contracts/my_contract.yaml",
  "source_path": "s3://bucket/input/data.csv",
  "target_path": "s3://bucket/output/data.csv"
}
```

You can also use local paths for testing:
```json
{
  "contract_path": "contracts/my_contract.yaml",
  "source_path": "examples/sample_data.csv",
  "target_path": "output/results.csv"
}
```

## Function Output

**Success:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "Data contract execution completed successfully",
    "contract": "Contract Name",
    "input_rows": 100,
    "output_rows": 100,
    "pipeline_results": {
      "success": true
    }
  }
}
```

### Error Response
```json
{
  "statusCode": 500,
  "body": {
    "message": "Data contract execution failed: error details"
  }
}
```

## Configuration

**Memory & Timeout**:
- Memory: 256MB (suitable for < 500MB files)
- Timeout: 30 seconds (increase for larger datasets)
- Ephemeral Storage: 512MB

To increase:
```bash
aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --memory-size 512 \
  --timeout 60
```

## Updating the Function

After code changes:

```bash
cd lambda_build
zip -r ../lambda_function.zip .
cd ..

aws lambda update-function-code \
  --function-name data-contract-executor \
  --zip-file fileb://lambda_function.zip
```

## Monitoring

View logs:
```bash
aws logs tail /aws/lambda/data-contract-executor --follow
```

View metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=data-contract-executor \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average,Maximum
```

## Troubleshooting

**"No module named 'pandas'"**
Include pandas in the deployment package:
```bash
pip install pandas -t lambda_build/
cd lambda_build && zip -r ../lambda_function.zip . && cd ..
```

**"Access Denied" on S3**
- Verify IAM role has S3 permissions
- Check bucket name and path
- Test: `aws s3 ls s3://your-bucket/`

**"Timeout exceeded"**
- Dataset is too large
- Increase timeout and memory:
```bash
aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --memory-size 512 \
  --timeout 60
```

**"OutOfMemory" errors**
- Dataset exceeds Lambda memory
- Increase memory allocation or process in smaller chunks

## Cost Estimation

For 100 invocations/month:
- Lambda: ~$0.20 (first 1M requests free)
- S3: ~$0.023/GB transferred
- CloudWatch: Usually free tier

Typical monthly cost is under $1 for light usage.

## Best Practices

1. Keep datasets under 500MB
2. Schedule with EventBridge for regular validation
3. Monitor CloudWatch logs regularly
4. Test locally first using QUICKSTART.md examples
5. Track contract changes with versioning

## Scheduled Execution

Run validation daily using EventBridge:

```bash
aws events put-rule \
  --name daily-data-validation \
  --schedule-expression "cron(0 2 * * ? *)"

aws events put-targets \
  --rule daily-data-validation \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:data-contract-executor","Input"='{"contract_path":"contracts/sample_contract.yaml"}'
```

## Cleanup

```bash
aws lambda delete-function --function-name data-contract-executor

aws iam delete-role-policy \
  --role-name DataContractExecutorRole \
  --policy-name DataContractS3Access

aws iam detach-role-policy \
  --role-name DataContractExecutorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name DataContractExecutorRole
```

See [QUICKSTART.md](QUICKSTART.md), [README.md](README.md), and [examples/](examples/) for more information.
