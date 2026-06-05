# PoC - Construction Disruptor

PoC personal project. Portal for customers and internal operations to order, administer and track items. Provides sign up and sign in options for a customer, sign in options only for internal admin

Integrated with Gemini LLM so orders can be placed in a natural tone rather than from an item list, as well as being able to scope out the needs for a project to order

Front End - Hosted on Streamlit, Language: Python

Back End - Hosted on Suprabase (Psybase - Slowly changing dimensions), Language SQL

Connection mechanism: API

Unit case integration included via github workflows

https://poc---construction-disruptor-gpnpwremppmzfds9mfcun3.streamlit.app

Note: There are instances where the app behind the URL is dormant. If it is and you want to see, just message me

Automated Pipeline tests
1. Zero-Crash UI Thread Assembly
The framework used Streamlit's headless engine to physically compile and execute app.py. It proved that:
•	The Entire Imports Matrix is Sound: Your application successfully found and loaded heavy data-science and database libraries (pandas, plotly, and supabase) without hitting a single missing module or dependency conflict.
•	The App Launches Cleanly: The layout handles its initial execution thread without throwing standard python syntax errors, structural layout runtime exceptions, or broken variable assignments on startup.
2. Multi-Tier Third-Party Library Integration
Before this test, we only knew that custom Python code worked. This functional pass validates that your app is talking to its dependencies correctly:
•	Data Visualization Prep: The plotly.express engine initializes cleanly within the Streamlit canvas context.
•	Database Client Initialization: The supabase client library loads successfully and reads your credentials architecture without throwing authorization object-instantiation faults.
3. User Interaction & Core Event Loop Simulation
The test simulates a headless browser session acting exactly like an end-user visiting your site:
•	Input Injection Validation: The system successfully targets your text entry boxes and numerical input fields, typing in simulated user metrics (like project names or financial thresholds) to verify they accept data inputs cleanly.
•	Component Re-run Cycle: The test clicks your interface buttons, forcing Streamlit to clear its state, refresh its internal layout engine, re-run from top to bottom with the new data matrix, and process the results successfully without crashing.
