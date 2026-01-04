"""Unit tests for Lambda handler."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from engine.contract_parser import DataContract
from runtime.lambda_handler import handler


class TestLambdaHandler:
    """Test Lambda handler function."""
    
    @patch("runtime.lambda_handler._read_csv_from_s3")
    @patch("runtime.lambda_handler._write_csv_to_s3")
    @patch("runtime.lambda_handler.load_contract")
    def test_handler_success(self, mock_load_contract, mock_write_csv, mock_read_csv):
        """Test successful lambda handler execution."""
        # Create a mock contract
        contract_dict = {
            "name": "Test Contract",
            "version": "1.0",
            "source_s3_path": "s3://bucket/input.csv",
            "target_s3_path": "s3://bucket/output.csv",
            "schema": {
                "columns": {
                    "id": "integer",
                    "name": "string"
                }
            },
            "sla": {
                "min_rows": 1,
                "max_rows": 1000
            },
            "transformations": []
        }
        contract = DataContract(contract_dict)
        mock_load_contract.return_value = contract
        
        # Create a mock dataframe
        mock_read_csv.return_value = pd.DataFrame({
            "id": [1, 2],
            "name": ["John", "Jane"]
        })
        
        # Test event
        event = {
            "contract_path": "contracts/sample_contract.yaml"
        }
        context = Mock()
        
        # Execute handler
        result = handler(event, context)
        
        # Assertions
        assert result["statusCode"] == 200
        assert "Data contract execution completed successfully" in result["body"]
    
    @patch("runtime.lambda_handler.load_contract")
    def test_handler_missing_contract_path(self, mock_load_contract):
        """Test handler with missing contract path."""
        event = {}
        context = Mock()
        
        result = handler(event, context)
        
        assert result["statusCode"] == 500
        assert "contract_path" in result["body"]
    
    @patch("runtime.lambda_handler.load_contract")
    def test_handler_missing_s3_paths(self, mock_load_contract):
        """Test handler with contract missing S3 paths."""
        contract_dict = {
            "name": "Test Contract",
            "version": "1.0",
            "schema": {"columns": {}},
            "sla": {}
        }
        contract = DataContract(contract_dict)
        mock_load_contract.return_value = contract
        
        event = {
            "contract_path": "contracts/sample_contract.yaml"
        }
        context = Mock()
        
        result = handler(event, context)
        
        assert result["statusCode"] == 500
