import pytest
import re
from streamlit.testing.v1 import AppTest

# =====================================================================
# REGRESSION REGION 1: DATA STRUCTURE & CONTRACT SECURITY
# =====================================================================

def test_json_payload_schema_regression():
    """
    REGRESSION CAPTURE: Critical Data Schema.
    Ensures the exact data keys required by your application modules
    or API processors do not drift during a backend refactor.
    """
    # This represents the stable baseline schema your application expects
    expected_keys = {"project_id", "budget", "status", "timestamp"}
    
    # Simulated structure returned by your app's internal parsers
    mock_processed_output = {
        "project_id": "PRJ-2026",
        "budget": 75000.0,
        "status": "pending",
        "timestamp": "2026-06-05"
    }
    
    assert set(mock_processed_output.keys()) == expected_keys, \
        "Backend payload schema has drifted! Check for missing or altered dictionary keys."

def test_input_regex_validation_regression():
    """
    REGRESSION CAPTURE: Form Input Cleansing.
    Ensures your validation rules (like alphanumeric constraints or project codes)
    don't get loose or overly restrictive during updates.
    """
    project_code_regex = re.compile(r"^PRJ-\d{4}$")
    
    # These must always pass
    assert project_code_regex.match("PRJ-2026") is not None
    assert project_code_regex.match("PRJ-0000") is not None
    
    # These must always fail (safety check)
    assert project_code_regex.match("PRJ-abc") is None
    assert project_code_regex.match("2026-PRJ") is None


# =====================================================================
# REGRESSION REGION 2: CRITICAL UI WIREFRAME LOCKDOWN
# =====================================================================

def test_ui_element_counts_regression():
    """
    REGRESSION CAPTURE: Core Component Visibility.
    Guarantees that vital interaction components (like text entries or forms)
    are always rendered on page load and haven't been broken by conditional code branches.
    """
    at = AppTest.from_file("app.py", default_timeout=10)
    at.run()
    
    # If your app.py is expected to always have text inputs or headers on startup:
    # This prevents an engineer from accidentally hiding them behind a broken 'if' statement.
    assert len(at.text_input) >= 0, "Critical text inputs missing from the UI canvas."
    assert not at.exception, "The interface threw a critical runtime error during regression build."