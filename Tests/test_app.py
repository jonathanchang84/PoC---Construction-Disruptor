import pytest
import streamlit as st

# =====================================================================
# UNIT TESTING: CALCULATION & ARCHITECTURE CHECKS
# =====================================================================

def data_processor(budget: float, allocation_pct: float) -> float:
    """Core calculation logic (normally imported from your src library)."""
    if budget < 0 or allocation_pct < 0:
        raise ValueError("Financial metrics cannot be negative.")
    return round(budget * (allocation_pct / 100.0), 2)


def test_data_processor_calculation():
    """Verify that the allocation engine calculates percentages correctly."""
    assert data_processor(150000.00, 15.5) == 23250.00
    assert data_processor(0.0, 50.0) == 0.0


def test_data_processor_negative_boundary():
    """Verify that negative inputs trigger the expected structural exceptions."""
    with pytest.raises(ValueError):
        data_processor(-100.0, 10.0)


def test_pipeline_secrets_presence():
    """Validate that the application configuration strings are present and populated."""
    # Verifies the system can find the configuration keys without enforcing specific mock strings
    assert "SUPABASE_URL" in st.secrets
    assert len(st.secrets["SUPABASE_URL"]) > 0
    
    assert "SUPABASE_KEY" in st.secrets
    assert len(st.secrets["SUPABASE_KEY"]) > 0