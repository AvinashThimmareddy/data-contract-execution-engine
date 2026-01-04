"""Contract parser module for reading and validating data contracts."""

import yaml
from typing import Dict, Any


class DataContract:
    """Represents a data contract with schema, SLA rules, and S3 paths."""
    
    def __init__(self, contract_dict: Dict[str, Any]):
        """
        Initialize a data contract from a dictionary.
        
        Args:
            contract_dict: Dictionary containing contract definition
        """
        self.name = contract_dict.get("name", "unknown")
        self.version = contract_dict.get("version", "1.0")
        self.source_s3_path = contract_dict.get("source_s3_path")
        self.target_s3_path = contract_dict.get("target_s3_path")
        self.schema = contract_dict.get("schema", {})
        self.sla = contract_dict.get("sla", {})
        self.transformations = contract_dict.get("transformations", [])
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema definition."""
        return self.schema
    
    def get_sla(self) -> Dict[str, Any]:
        """Get the SLA rules."""
        return self.sla
    
    def get_transformations(self) -> list:
        """Get the transformations to apply."""
        return self.transformations


def load_contract(contract_path: str) -> DataContract:
    """
    Load a data contract from a YAML file.
    
    Args:
        contract_path: Path to the contract YAML file (local or S3)
        
    Returns:
        DataContract object
        
    Raises:
        FileNotFoundError: If contract file not found
        ValueError: If contract format is invalid
    """
    try:
        # Handle S3 paths
        if contract_path.startswith("s3://"):
            import boto3
            s3_client = boto3.client("s3")
            bucket, key = contract_path.replace("s3://", "").split("/", 1)
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            content = obj["Body"].read().decode("utf-8")
        else:
            with open(contract_path, "r") as f:
                content = f.read()
        
        # Parse YAML
        contract_dict = yaml.safe_load(content)
        return DataContract(contract_dict)
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    except Exception as e:
        raise ValueError(f"Failed to load contract: {str(e)}")
