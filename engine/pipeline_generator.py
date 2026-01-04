"""Pipeline generator for executing data validation and transformation pipelines."""

import pandas as pd
from typing import Dict, Any
from engine.validation_engine import ValidationEngine
from engine.sla_enforcer import SLAEnforcer


class PipelineGenerator:
    """Generates and executes data validation pipelines from contracts."""
    
    def __init__(self, contract):
        """
        Initialize pipeline generator with a contract.
        
        Args:
            contract: DataContract object
        """
        self.contract = contract
        self.validation_engine = ValidationEngine(contract.get_schema())
        self.sla_enforcer = SLAEnforcer(contract.get_sla())
        self.pipeline_results = {}
    
    def generate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate and execute the validation pipeline.
        
        Args:
            df: Input Pandas DataFrame
            
        Returns:
            Dictionary with pipeline results
        """
        self.pipeline_results = {
            "input_rows": len(df),
            "steps": [],
            "success": True
        }
        
        # Step 1: Validate schema
        schema_valid = self.validation_engine.validate_schema(df)
        self.pipeline_results["steps"].append({
            "name": "schema_validation",
            "status": "passed" if schema_valid else "failed",
            "details": f"Schema validation {'passed' if schema_valid else 'failed'}"
        })
        
        if not schema_valid:
            self.pipeline_results["success"] = False
            return self.pipeline_results
        
        # Step 2: Validate data quality
        quality_results = self.validation_engine.validate_data_quality(df)
        self.pipeline_results["steps"].append({
            "name": "data_quality",
            "status": "completed",
            "details": quality_results
        })
        
        # Step 3: Enforce SLA
        sla_results = self.sla_enforcer.enforce_sla(df)
        self.pipeline_results["steps"].append({
            "name": "sla_enforcement",
            "status": "passed" if sla_results["sla_passed"] else "failed",
            "details": sla_results
        })
        
        if not sla_results["sla_passed"]:
            self.pipeline_results["success"] = False
        
        return self.pipeline_results
    
    def get_results(self) -> Dict[str, Any]:
        """Get pipeline execution results."""
        return self.pipeline_results
