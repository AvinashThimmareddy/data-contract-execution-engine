"""Validation engine for runtime data validation against contracts."""

import pandas as pd
from typing import Dict, Any, List


class ValidationEngine:
    """Validates data against contract schema and constraints."""
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize validation engine with schema.
        
        Args:
            schema: Dictionary describing the expected schema
        """
        self.schema = schema
    
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validate dataframe schema against contract schema.
        
        Args:
            df: Pandas DataFrame to validate
            
        Returns:
            True if schema is valid, False otherwise
        """
        try:
            contract_columns = self.schema.get("columns", {})
            
            # Check if all required columns exist
            for col_name in contract_columns.keys():
                if col_name not in df.columns:
                    print(f"Missing required column: {col_name}")
                    return False
            
            return True
        except Exception as e:
            print(f"Schema validation error: {str(e)}")
            return False
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality metrics.
        
        Args:
            df: Pandas DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "total_rows": len(df),
            "null_counts": {},
            "duplicate_rows": 0,
            "validation_passed": True
        }
        
        try:
            # Check for nulls in each column
            for col in df.columns:
                null_count = df[col].isna().sum()
                results["null_counts"][col] = int(null_count)
            
            # Check for duplicates
            duplicate_rows = len(df) - len(df.drop_duplicates())
            results["duplicate_rows"] = duplicate_rows
            
            return results
        except Exception as e:
            results["validation_passed"] = False
            results["error"] = str(e)
            return results
    
    def validate_constraints(self, df: pd.DataFrame, constraints: List[Dict[str, Any]]) -> bool:
        """
        Validate custom constraints.
        
        Args:
            df: Pandas DataFrame to validate
            constraints: List of constraint definitions
            
        Returns:
            True if all constraints are satisfied
        """
        try:
            for constraint in constraints:
                constraint_type = constraint.get("type")
                column = constraint.get("column")
                value = constraint.get("value")
                
                if constraint_type == "not_null":
                    null_count = df[column].isna().sum()
                    if null_count > 0:
                        print(f"Constraint violation: {column} has {null_count} null values")
                        return False
                
                elif constraint_type == "min_value":
                    min_val = df[column].min()
                    if min_val < value:
                        print(f"Constraint violation: {column} minimum value {min_val} is less than {value}")
                        return False
                
                elif constraint_type == "max_value":
                    max_val = df[column].max()
                    if max_val > value:
                        print(f"Constraint violation: {column} maximum value {max_val} is greater than {value}")
                        return False
            
            return True
        except Exception as e:
            print(f"Constraint validation error: {str(e)}")
            return False
