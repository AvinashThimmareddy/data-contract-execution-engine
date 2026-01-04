# AWS Lambda Deployment Guide

Simple guide to deploy the Data Contract Execution Engine to AWS Lambda.

## Prerequisites

- AWS Account with Lambda and S3 permissions
- AWS CLI configured: `aws configure`
- Python 3.7+
- Git

## Quick Start (5 minutes)

### 1. Create Deployment Package

**On Mac/Linux:**
```bash
# Clone repository
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine

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
```

**On Windows (PowerShell):**
```powershell
# Clone repository
git clone https://github.com/<your-username>/data-contract-execution-engine.git
cd data-contract-execution-engine

# Create deployment package
mkdir lambda_build
Copy-Item -Path engine -Destination lambda_build -Recurse
Copy-Item -Path runtime -Destination lambda_build -Recurse
Copy-Item -Path contracts -Destination lambda_build -Recurse
Copy-Item -Path requirements.txt -Destination lambda_build

# Create ZIP (no installation needed)
Compress-Archive -Path lambda_build/* -DestinationPath lambda_function.zip -Force
```

### 2. Create IAM Role

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

### 3. Create Lambda Function

```bash
# Get your AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create function
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

### 4. Test the Function

Create test event (`test_event.json`):
```json
{
  "contract_path": "contracts/sample_contract.yaml",
  "source_s3_path": "s3://my-bucket/input/data.csv",
  "target_s3_path": "s3://my-bucket/output/data_validated.csv"
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

## Function Input Format

The function accepts two input patterns:

**Pattern 1: With S3 paths in event**
```json
{
  "contract_path": "contracts/my_contract.yaml",
  "source_s3_path": "s3://bucket/input/data.csv",
  "target_s3_path": "s3://bucket/output/data.csv"
}
```

**Pattern 2: Using contract S3 paths**
```json
{
  "contract_path": "contracts/my_contract.yaml"
}
```
(Contract must contain `source_s3_path` and `target_s3_path`)

## Function Output

### Success Response
```json
{
  "statusCode": 200,
  "body": {
    "message": "Data contract execution completed successfully",
    "contract": "Contract Name",
    "input_rows": 100,
    "output_rows": 100,
    "pipeline_results": {
      "success": true,
      "steps": [...]
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

### Memory & Timeout
- **Memory**: 256MB (default, suitable for < 500MB files)
- **Timeout**: 30 seconds (adjust for larger datasets)
- **Ephemeral Storage**: 512MB

Increase for larger datasets:
```bash
aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --memory-size 512 \
  --timeout 60
```

### Environment Variables (Optional)
```bash
aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --environment Variables={LOG_LEVEL=INFO}
```

## Updating the Function

After making code changes:

```bash
# Rebuild package
cd lambda_build
zip -r ../lambda_function.zip .
cd ..

# Update function
aws lambda update-function-code \
  --function-name data-contract-executor \
  --zip-file fileb://lambda_function.zip
```

## Monitoring

### View Logs
```bash
# Stream logs in real-time
aws logs tail /aws/lambda/data-contract-executor --follow

# Get specific invocation logs
aws lambda invoke \
  --function-name data-contract-executor \
  --payload file://test_event.json \
  --log-type Tail \
  response.json
```

### View Metrics
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

### "No module named 'pandas'"
Include pandas in the deployment package:
```bash
pip install pandas -t lambda_build/
cd lambda_build && zip -r ../lambda_function.zip . && cd ..
```

### "Access Denied" on S3
- Verify IAM role has S3 permissions
- Check S3 bucket name and path are correct
- Test: `aws s3 ls s3://your-bucket/`

### "Timeout exceeded"
- Dataset is too large
- Increase timeout/memory or split data into smaller files
```bash
aws lambda update-function-configuration \
  --function-name data-contract-executor \
  --memory-size 512 \
  --timeout 60
```

### "OutOfMemory" errors
- Dataset exceeds Lambda memory
- Increase memory allocation
- Or process in smaller chunks

## Cost Estimation

For 100 invocations/month:
- **Lambda**: ~$0.20 (first 1M requests free)
- **S3**: ~$0.023/GB transferred
- **CloudWatch**: Usually free tier

**Typical monthly cost: < $1** for light usage

## Best Practices

1. **Keep datasets small**: Optimal < 500MB
2. **Schedule with EventBridge**: For regular validation
3. **Monitor logs**: Check CloudWatch regularly
4. **Test locally first**: Use QUICKSTART.md examples
5. **Version contracts**: Track contract changes

## Advanced: Scheduled Execution

Run validation on schedule using EventBridge:

```bash
# Create EventBridge rule (daily at 2 AM UTC)
aws events put-rule \
  --name daily-data-validation \
  --schedule-expression "cron(0 2 * * ? *)"

# Add Lambda target
aws events put-targets \
  --rule daily-data-validation \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:data-contract-executor","Input"='{"contract_path":"contracts/sample_contract.yaml"}'
```

## Cleanup

```bash
# Delete function
aws lambda delete-function --function-name data-contract-executor

# Delete IAM role and policy
aws iam delete-role-policy \
  --role-name DataContractExecutorRole \
  --policy-name DataContractS3Access

aws iam detach-role-policy \
  --role-name DataContractExecutorRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam delete-role --role-name DataContractExecutorRole
```

## See Also

- [QUICKSTART.md](QUICKSTART.md) - Local testing guide
- [README.md](README.md) - Project overview
- [examples/](examples/) - Example files
