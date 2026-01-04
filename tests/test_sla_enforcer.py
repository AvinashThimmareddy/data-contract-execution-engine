"""Unit tests for SLA enforcer module."""

import pytest
import pandas as pd
from engine.sla_enforcer import SLAEnforcer


class TestSLAEnforcer:
    """Test SLAEnforcer class."""
    
    def test_sla_enforcer_initialization(self):
        """Test SLAEnforcer initialization."""
        sla_rules = {"min_rows": 10, "max_rows": 1000}
        enforcer = SLAEnforcer(sla_rules)
        assert enforcer.sla_rules == sla_rules
    
    def test_enforce_sla_min_rows_passed(self):
        """Test min_rows SLA enforcement (passed)."""
        sla_rules = {"min_rows": 2}
        enforcer = SLAEnforcer(sla_rules)
        
        df = pd.DataFrame({
            "id": [1, 2, 3]
        })
        
        results = enforcer.enforce_sla(df)
        assert results["sla_passed"] is True
        assert results["metrics"]["row_count"] == 3
    
    def test_enforce_sla_min_rows_failed(self):
        """Test min_rows SLA enforcement (failed)."""
        sla_rules = {"min_rows": 10}
        enforcer = SLAEnforcer(sla_rules)
        
        df = pd.DataFrame({
            "id": [1, 2]
        })
        
        results = enforcer.enforce_sla(df)
        assert results["sla_passed"] is False
        assert len(results["violations"]) > 0
    
    def test_enforce_sla_max_rows_passed(self):
        """Test max_rows SLA enforcement (passed)."""
        sla_rules = {"max_rows": 10}
        enforcer = SLAEnforcer(sla_rules)
        
        df = pd.DataFrame({
            "id": [1, 2]
        })
        
        results = enforcer.enforce_sla(df)
        assert results["sla_passed"] is True
    
    def test_enforce_sla_completeness_passed(self):
        """Test completeness SLA enforcement (passed)."""
        sla_rules = {"completeness_threshold": 0.8}
        enforcer = SLAEnforcer(sla_rules)
        
        df = pd.DataFrame({
            "id": [1, 2, None],
            "name": ["John", "Jane", "Bob"]
        })
        
        results = enforcer.enforce_sla(df)
        assert results["sla_passed"] is True
        assert results["metrics"]["completeness"] > 0.8
    
    def test_enforce_sla_completeness_failed(self):
        """Test completeness SLA enforcement (failed)."""
        sla_rules = {"completeness_threshold": 0.95}
        enforcer = SLAEnforcer(sla_rules)
        
        df = pd.DataFrame({
            "id": [1, 2, None],
            "name": [None, None, "Bob"]
        })
        
        results = enforcer.enforce_sla(df)
        assert results["sla_passed"] is False
        assert len(results["violations"]) > 0
