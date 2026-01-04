"""Unit tests for pipeline generator module."""

import pytest
import pandas as pd
from engine.contract_parser import DataContract
from engine.pipeline_generator import PipelineGenerator


@pytest.fixture
def sample_contract():
    """Sample contract for testing."""
    contract_dict = {
        "name": "Test Contract",
        "version": "1.0",
        "source_s3_path": "s3://bucket/input.csv",
        "target_s3_path": "s3://bucket/output.csv",
        "schema": {
            "columns": {
                "id": "integer",
                "name": "string",
                "email": "string"
            }
        },
        "sla": {
            "min_rows": 1,
            "max_rows": 1000,
            "completeness_threshold": 0.9
        },
        "transformations": []
    }
    return DataContract(contract_dict)


class TestPipelineGenerator:
    """Test PipelineGenerator class."""
    
    def test_pipeline_generator_initialization(self, sample_contract):
        """Test PipelineGenerator initialization."""
        generator = PipelineGenerator(sample_contract)
        assert generator.contract == sample_contract
    
    def test_pipeline_generate_success(self, sample_contract):
        """Test successful pipeline generation."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["John", "Jane", "Bob"],
            "email": ["john@example.com", "jane@example.com", "bob@example.com"]
        })
        
        generator = PipelineGenerator(sample_contract)
        results = generator.generate(df)
        
        assert results is not None
        assert results["success"] is True
        assert results["input_rows"] == 3
    
    def test_pipeline_generate_schema_validation_failure(self, sample_contract):
        """Test pipeline generation with schema validation failure."""
        # Create dataframe with missing required column
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["john", "jane"]
        })
        
        generator = PipelineGenerator(sample_contract)
        results = generator.generate(df)
        
        assert results["success"] is False
    
    def test_pipeline_generate_sla_failure(self):
        """Test pipeline generation with SLA failure."""
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
                "min_rows": 100  # More than our test data
            }
        }
        contract = DataContract(contract_dict)
        
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["john", "jane"]
        })
        
        generator = PipelineGenerator(contract)
        results = generator.generate(df)
        
        assert results["success"] is False
