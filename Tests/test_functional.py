import pytest
from streamlit.testing.v1 import AppTest

def test_app_render_and_submission():
    """Simulate a user filling out a form and clicking a button in app.py."""
    
    # 1. Initialize and start the headless Streamlit application
    at = AppTest.from_file("app.py", default_timeout=10)
    at.run()
    
    # Assert that the app loaded successfully and didn't throw an unhandled exception
    assert not at.exception, f"App crashed on startup with: {at.exception}"
    
    # 2. Simulate User Input
    # Let's say your app.py has a text input field for a project title or budget
    # AppTest exposes elements via lists like .text_input, .number_input, etc.
    if at.text_input:
        # Simulate typing 'Disruptor PoC' into the first text input field found
        at.text_input[0].input("Disruptor PoC").run()
        
    if at.number_input:
        # Simulate typing '50000' into the first numeric input box found
        at.number_input[0].input(50000).run()

    # 3. Simulate a Button Click
    # Let's say you have an st.button("Run Analysis") or st.button("Submit")
    if at.button:
        # Click the first button on the page and re-run the app to process inputs
        at.button[0].click().run()
        
        # 4. Assert Output Behavior
        # Verify that an exception didn't happen after submitting the data
        assert not at.exception
        
        # Check that expected output text or status messages appeared on screen
        # (e.g., verifying st.success() or st.write() text blocks)
        # assert "Success" in at.markdown[0].value