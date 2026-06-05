# PoC - Construction Disruptor

PoC personal project. Portal for customers and internal operations to order, administer and track items. Provides sign up and sign in options for a customer, sign in options only for internal admin

Integrated with Gemini LLM so orders can be placed in a natural tone rather than from an item list, as well as being able to scope out the needs for a project to order

Front End - Hosted on Streamlit, Language: Python

Back End - Hosted on Suprabase (Psybase - Slowly changing dimensions), Language SQL

Connection mechanism: API

Unit case integration included via github workflows

https://poc---construction-disruptor-gpnpwremppmzfds9mfcun3.streamlit.app

Note: There are instances where the app behind the URL is dormant. If it is and you want to see, just message me

**Automated Unit tests**
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

**Automated Regression Tests**
1. Data Contract & Schema Lock (test_json_payload_schema_regression)
When your application passes information between its processing functions, the database, or an external API like Gemini, it relies on a specific "contract"—meaning a precise dictionary of data keys.
•	What it checked: It verified that a processed project output dictionary contains the exact four keys your application expects: project_id, budget, status, and timestamp.
•	Why this prevents a regression: If you or another engineer refactor your backend code three months from now and accidentally capitalize a key (like changing project_id to Project_ID) or drop a column, this test will immediately fail. It alerts you before that broken data contract reaches your UI or corrupts your Supabase tables.
2. Input Validation Rules Lock (test_input_regex_validation_regression)
Applications often use regular expressions (Regex) to ensure user inputs are clean, standardized, and safe from malicious injection or bad formatting.
•	What it checked: It ran a series of assertions against a standard project tracking format (PRJ-XXXX). It proved that valid strings (like PRJ-2026) are permitted, while invalid structures (like text strings PRJ-abc or reversed formats 2026-PRJ) are strictly blocked.
•	Why this prevents a regression: When you tweak validation code down the line to accommodate a new feature, it's easy to accidentally make the rules too loose (allowing garbage data into your system) or too restrictive (breaking forms for legitimate users). This test locks the boundaries in place.
3. Interface Canvas Guard (test_ui_element_counts_regression)
Streamlit dynamically paints components onto the screen as code executes sequentially from top to bottom. If a logic branch (if/else statement) breaks, an entire section of your website can completely vanish.
•	What it checked: It ran your actual app.py script headlessly and verified that vital user-interaction components (like your text entry fields) are present and accounted for on startup.
•	Why this prevents a regression: It guarantees that optimizing your backend code hasn't accidentally caused a catastrophic frontend UI regression, ensuring your users will always see the fields they need to interact with the app.
