"""Unit tests for validation engine module."""

import pytest
import pandas as pd
from engine.validation_engine import ValidationEngine


@pytest.fixture
def sample_schema():
    """Sample schema for testing."""
    return {
        "columns": {
            "id": "integer",
            "name": "string",
            "email": "string"
        }
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["John", "Jane", "Bob"],
        "email": ["john@example.com", "jane@example.com", "bob@example.com"]
    })


class TestValidationEngine:
    """Test ValidationEngine class."""
    
    def test_validation_engine_initialization(self, sample_schema):
        """Test ValidationEngine initialization."""
        engine = ValidationEngine(sample_schema)
        assert engine.schema == sample_schema
    
    def test_validate_schema_valid(self, sample_schema, sample_dataframe):
        """Test schema validation with valid schema."""
        engine = ValidationEngine(sample_schema)
        assert engine.validate_schema(sample_dataframe) is True
    
    def test_validate_schema_invalid(self, sample_schema):
        """Test schema validation with invalid schema."""
        engine = ValidationEngine(sample_schema)
        
        # DataFrame missing required column
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["John", "Jane"]
        })
        
        assert engine.validate_schema(df) is False
    
    def test_validate_data_quality(self):
        """Test data quality validation."""
        engine = ValidationEngine({})
        
        df = pd.DataFrame({
            "id": [1, 2, None],
            "name": ["John", "Jane", "Bob"]
        })
        
        results = engine.validate_data_quality(df)
        assert results["total_rows"] == 3
        assert results["null_counts"]["id"] == 1
        assert results["null_counts"]["name"] == 0
    
    def test_validate_constraints_not_null(self):
        """Test not_null constraint validation."""
        engine = ValidationEngine({})
        
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["John", None]
        })
        
        constraints = [{"type": "not_null", "column": "name"}]
        assert engine.validate_constraints(df, constraints) is False
    
    def test_validate_constraints_min_value(self):
        """Test min_value constraint validation."""
        engine = ValidationEngine({})
        
        df = pd.DataFrame({
            "age": [18, 25, 30]
        })
        
        constraints = [{"type": "min_value", "column": "age", "value": 18}]
        assert engine.validate_constraints(df, constraints) is True
        
        constraints = [{"type": "min_value", "column": "age", "value": 20}]
        assert engine.validate_constraints(df, constraints) is False
