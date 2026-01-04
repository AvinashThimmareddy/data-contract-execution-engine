"""Unit tests for contract parser module."""

import pytest
import tempfile
import yaml
from engine.contract_parser import load_contract, DataContract


class TestDataContract:
    """Test DataContract class."""
    
    def test_data_contract_initialization(self):
        """Test DataContract initialization."""
        contract_dict = {
            "name": "Test Contract",
            "version": "1.0",
            "source_s3_path": "s3://bucket/input.csv",
            "target_s3_path": "s3://bucket/output.csv",
            "schema": {"columns": {"id": "integer"}},
            "sla": {"min_rows": 1},
            "transformations": []
        }
        contract = DataContract(contract_dict)
        
        assert contract.name == "Test Contract"
        assert contract.version == "1.0"
        assert contract.source_s3_path == "s3://bucket/input.csv"
        assert contract.target_s3_path == "s3://bucket/output.csv"
        assert contract.get_schema() == {"columns": {"id": "integer"}}
        assert contract.get_sla() == {"min_rows": 1}
        assert contract.get_transformations() == []
    
    def test_data_contract_defaults(self):
        """Test DataContract with default values."""
        contract = DataContract({})
        
        assert contract.name == "unknown"
        assert contract.version == "1.0"
        assert contract.source_s3_path is None
        assert contract.target_s3_path is None
        assert contract.get_schema() == {}
        assert contract.get_sla() == {}


class TestLoadContract:
    """Test load_contract function."""
    
    def test_load_contract_from_yaml(self):
        """Test loading contract from YAML file."""
        contract_dict = {
            "name": "YAML Contract",
            "version": "1.0",
            "source_s3_path": "s3://bucket/input.csv",
            "target_s3_path": "s3://bucket/output.csv",
            "schema": {"columns": {"id": "integer"}},
            "sla": {"min_rows": 1}
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(contract_dict, f)
            f.flush()
            
            contract = load_contract(f.name)
            assert contract.name == "YAML Contract"
            assert contract.version == "1.0"
    
    def test_load_contract_file_not_found(self):
        """Test loading contract with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_contract("/non/existent/path.yaml")
    
    def test_load_contract_invalid_format(self):
        """Test loading contract with invalid format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("invalid content {{{")
            f.flush()
            
            with pytest.raises(ValueError):
                load_contract(f.name)
