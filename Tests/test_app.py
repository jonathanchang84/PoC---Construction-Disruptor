import pytest
import streamlit as st

# ==========================================
# 1. PLACEHOLDER FOR BACKEND FUNCTIONS
# ==========================================
# Tip: As your app grows, move business logic/calculations out of app.py 
# into helper files (like utils.py) so you can import and test them cleanly here.
def mock_data_processor(raw_value: float) -> float:
    """Example helper function processing numeric inputs."""
    if raw_value < 0:
        return 0.0
    return round(raw_value * 1.2, 2)


# ==========================================
# 2. THE TEST MATRIX
# ==========================================

def test_data_processor_calculation():
    """Verify core math calculations behave exactly as expected."""
    assert mock_data_processor(100) == 120.0
    assert mock_data_processor(10.55) == 12.66

def test_data_processor_negative_boundary():
    """Ensure edge cases (like negative numbers) are safely caught and normalized."""
    assert mock_data_processor(-50) == 0.0

def test_pipeline_secrets_presence():
    """Validate that the GitHub actions pipeline is injecting credentials correctly."""
    # This directly tests that our mock .streamlit/secrets.toml layer works!
    assert st.secrets["SUPABASE_URL"] == "https://mockinstance.supabase.co"
    assert st.secrets["GEMINI_API_KEY"] == "mock-gemini-key-string"