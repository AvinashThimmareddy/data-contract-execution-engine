"""AWS Lambda handler for Data Contract Execution Engine."""

import json
import logging
import boto3
import pandas as pd
from typing import Dict, Any
from io import StringIO
import os

from engine.contract_parser import load_contract
from engine.pipeline_generator import PipelineGenerator

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client
s3_client = boto3.client("s3")


def _is_s3_path(path: str) -> bool:
    """Check if path is S3 path (starts with s3://)."""
    return path.startswith("s3://")


def _read_csv(path: str) -> pd.DataFrame:
    """Read CSV file from S3 or local filesystem."""
    if _is_s3_path(path):
        return _read_csv_from_s3(path)
    else:
        return pd.read_csv(path)


def _write_csv(df: pd.DataFrame, path: str) -> None:
    """Write CSV file to S3 or local filesystem."""
    if _is_s3_path(path):
        _write_csv_to_s3(df, path)
    else:
        # Ensure directory exists for local paths
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        df.to_csv(path, index=False)


def _read_contract(path: str) -> str:
    """Read contract file from S3 or local filesystem."""
    if _is_s3_path(path):
        bucket, key = path.replace("s3://", "").split("/", 1)
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read().decode("utf-8")
    else:
        with open(path, "r") as f:
            return f.read()


def _read_csv_from_s3(s3_path: str) -> pd.DataFrame:
    """Read CSV file from S3 path."""
    bucket, key = s3_path.replace("s3://", "").split("/", 1)
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj["Body"])
    return df


def _write_csv_to_s3(df: pd.DataFrame, s3_path: str) -> None:
    """Write CSV file to S3 path."""
    bucket, key = s3_path.replace("s3://", "").split("/", 1)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for data contract execution.
    
    Supports both S3 and local file paths for contract, source, and target.
    
    Args:
        event: Lambda event containing:
            - contract_path: Path to contract file (s3://bucket/key or /local/path)
            - source_path: Path to source data file (S3 or local, overrides contract)
            - target_path: Path to target data file (S3 or local, overrides contract)
        context: Lambda context object
    
    Returns:
        Dictionary with execution status and results
    
    Examples:
        # S3-based execution (Lambda deployment)
        {
            "contract_path": "s3://my-bucket/contracts/sample_contract.yaml",
            "source_path": "s3://my-bucket/data/customers.csv",
            "target_path": "s3://my-bucket/results/customers_validated.csv"
        }
        
        # Local execution (local testing)
        {
            "contract_path": "contracts/sample_contract.yaml",
            "source_path": "examples/customers.csv",
            "target_path": "output/customers_validated.csv"
        }
    """
    try:
        logger.info("Data Contract Execution Engine - Lambda Handler Started")
        
        # Extract parameters from event
        contract_path = event.get("contract_path")
        
        if not contract_path:
            raise ValueError("Missing required parameter: contract_path")
        
        logger.info(f"Processing contract: {contract_path}")
        
        # Load contract (direct YAML reading since contract_parser uses load_contract)
        logger.info("Loading contract...")
        contract = load_contract(contract_path)
        logger.info(f"Contract loaded: {contract.name} v{contract.version}")
        
        # Get source and target paths (from event override or contract)
        source_path = event.get("source_path", contract.source_s3_path)
        target_path = event.get("target_path", contract.target_s3_path)
        
        if not source_path or not target_path:
            raise ValueError("Source and target paths must be specified in contract or event")
        
        logger.info(f"Source path: {source_path}")
        logger.info(f"Target path: {target_path}")
        
        # Read input data (supports both S3 and local)
        logger.info("Reading input data...")
        df = _read_csv(source_path)
        input_row_count = len(df)
        logger.info(f"Input data loaded: {input_row_count} rows")
        
        # Generate and execute pipeline
        logger.info("Generating and executing pipeline...")
        pipeline = PipelineGenerator(contract)
        pipeline_results = pipeline.generate(df)
        
        logger.info(f"Pipeline execution results: {json.dumps(pipeline_results, indent=2, default=str)}")
        
        if not pipeline_results.get("success", True):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Pipeline validation failed",
                    "results": pipeline_results
                })
            }
        
        # Write output data (supports both S3 and local)
        logger.info("Writing output data...")
        _write_csv(df, target_path)
        logger.info(f"Output data written: {len(df)} rows")
        
        # Return success
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data contract execution completed successfully",
                "contract": contract.name,
                "input_rows": input_row_count,
                "output_rows": len(df),
                "pipeline_results": pipeline_results
            }, default=str)
        }
    
    except Exception as e:
        logger.error(f"Error during data contract execution: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"Data contract execution failed: {str(e)}"
            })
        }

