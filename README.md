# PoC - Construction Disruptor

PoC personal project. Portal for customers and internal operations to order, administer and track items. Provides sign up and sign in options for a customer, sign in options only for internal admin

Integrated with Gemini LLM so orders can be placed in a natural tone rather than from an item list, as well as being able to scope out the needs for a project to order

https://poc---construction-disruptor-gpnpwremppmzfds9mfcun3.streamlit.app

Note: There are instances where the app behind the URL is dormant. If it is and you want to see, just message me

## 🏗️ Project Architecture

This application is built as a lightweight, real-time financial dashboard leveraging a modern python-native stack. It is designed to be highly reactive, secure, and compatible with the latest Python runtime environments.

### ⚙️ Tech Stack & Infrastructure
* **Frontend & Application Framework:** [Streamlit](https://streamlit.io/) (utilizing native, safe UI component layout mapping).
* **Data Manipulation:** [Pandas](https://pandas.pydata.org/) (for in-memory tabular data cross-rate generation).
* **Data Fetching:** Python `requests` communicating with RESTful endpoints.
* **Production Hosting:** [Streamlit Community Cloud](https://streamlit.io/cloud) integrated via GitHub CI/CD.

### 🔄 Data Flow & Logic Engine

The system architecture follows a unidirectional data flow to ensure fast load times and minimal API overhead:

1.  **API Ingestion Layer:** When a user loads the page, the application sends an asynchronous GET request to the Open Exchange Rates API (`open.er-api.com`). 
    
2.  **Server-Side Caching (`st.cache_data`):** To prevent rate-limiting and ensure institutional-grade loading speeds, the live data payload is cached securely for **30 minutes (1800 seconds)**. Sub-second currency conversions happen instantly entirely in-memory without re-pinging the external API.

3.  **State Management & Session Routing:** User interactions (such as updating volume or triggering the `⇄` swap button) mutate variables stored within `st.session_state`. This forces an isolated runtime rerun to re-evaluate mathematical cross-rates without destroying user preferences.

4.  **Cross-Rate Computation Engine:**
    Because the base API endpoint normalizes all global fiat assets against the US Dollar ($USD$), the calculation layer uses a standard triangular arbitrage formula to compute any random currency pair ($A \rightarrow B$):
    
    $$\text{Converted Amount} = \left( \frac{\text{Amount}}{\text{Rate}_A} \right) \times \text{Rate}_B$$

5.  **Native Rendering Engine:** The presentation layer processes the updated metrics and feeds them dynamically into native UI nodes (`st.metric` and `st.dataframe`), perfectly optimizing for both light and dark mode browsers securely.


## Testing Framework

This repository includes an automated testing suite to guarantee the runtime stability, data integrity, and integration health of the application. The suite is broken down into three distinct tiers: Unit, Regression, and Integration tests.

---

### 1. Automated Unit Tests
These tests focus on isolated verification of the foundational application execution layers and core event loops.

* **Zero-Crash UI Thread Assembly**
    * **The Entire Imports Matrix is Sound:** This application successfully finds and loads heavy data-science and database libraries (`pandas`, `plotly`, and `supabase`) without hitting missing modules or dependency conflicts.
    * **The App Launches Cleanly:** The layout handles its initial execution thread without throwing standard Python syntax errors, structural layout runtime exceptions, or broken variable assignments on startup.
* **Multi-Tier Third-Party Library Integration**
    * **Data Visualization Prep:** The `plotly.express` engine initializes cleanly within the Streamlit canvas context.
    * **Database Client Initialization:** The `supabase` client library loads successfully and reads this credentials architecture without throwing authorization object-instantiation faults.
* **User Interaction & Core Event Loop Simulation**
    * **Input Injection Validation:** The system successfully targets the text entry boxes and numerical input fields on this site, typing in simulated user metrics (like project names or financial thresholds) to verify they accept data inputs cleanly.
    * **Component Re-run Cycle:** The test clicks the interface buttons, forcing Streamlit to clear its state, refresh its internal layout engine, re-run from top to bottom with the new data matrix, and process the results successfully without crashing.

---

### 2. Automated Regression Tests
These tests act as protective boundaries to ensure that future feature additions or backend refactoring do not inadvertently break existing functionality.

* **Data Contract & Schema Lock (`test_json_payload_schema_regression`)**
    * **What it checks:** It verifies that a processed project output dictionary contains the exact four keys this application expects: `project_id`, `budget`, `status`, and `timestamp`.
    * **Why this prevents a regression:** If an engineer refactors this backend code down the line and accidentally capitalizes a key (like changing `project_id` to `Project_ID`) or drops a column, this test will immediately fail. It alerts the team before that broken data contract reaches the UI or corrupts the Supabase tables.
* **Input Validation Rules Lock (`test_input_regex_validation_regression`)**
    * **What it checks:** It runs a series of assertions against a standard project tracking format (`PRJ-XXXX`). It proves that valid strings (like `PRJ-2026`) are permitted, while invalid structures (like text strings `PRJ-abc` or reversed formats `2026-PRJ`) are strictly blocked.
    * **Why this prevents a regression:** When tweaking validation code to accommodate a new feature, it's easy to accidentally make rules too loose (allowing garbage data into this system) or too restrictive (breaking forms for legitimate users). This test locks the boundaries in place.
* **Interface Canvas Guard (`test_ui_element_counts_regression`)**
    * **What it checks:** It runs the actual `app.py` script headlessly and verifies that vital user-interaction components (like the text entry fields) are present and accounted for on startup.
    * **Why this prevents a regression:** Streamlit dynamically paints components onto the screen sequentially. If a logic branch (`if/else` statement) breaks, entire sections can vanish. This guarantees that backend optimizations haven't caused a catastrophic frontend UI regression, ensuring users always see the fields they need.

---

### 3. Automated Integration Tests
These tests conduct live end-to-end handshakes with external dependencies to ensure the external cloud runtime environments are operational.

* **The Database Handshake (`test_live_supabase_connection_and_crud`)**
    * **Network & DNS Routing:** It verifies that the local environment (or CI/CD cloud runner) can successfully find this specific database instance across the internet (`https://xydkpbmmwvxfftvsecuy.supabase.co`).
    * **Authentication & Permissions:** It passes the `SUPABASE_KEY` token to verify that the database server accepts this security clearance and does not reject the app with an HTTP `401 Unauthorized` or `403 Forbidden` error.
    * **Schema Integrity & State Check:** By intentionally pinging the backend, it confirms that the database engine is online, actively listening, and returning structural responses (like the `PGRST205` schema cache signal), proving that this database connection is 100% operational.
* **The AI Engine Handshake (`test_live_gemini_api_handshake`)**
    * **Credential Validation:** It ensures that this configuration environment has successfully mapped a real, live Google Gemini API key token string to the application layer.
    * **Production Environment Safeties:** It explicitly scans the credentials to ensure no `"mock-"` or dummy sandbox placeholder strings accidentally leaked into this production run. This guards against a cloud pipeline passing its checks while using fake data that would immediately crash the live app for a real user.
    * **API Routing Security:** It guarantees that the moment this application needs to route user inputs or prompt parameters out to Google's model engines, the authorization gate will slide open flawlessly.

### 🗺️ System Topology

```text
 [ User Browser ] 
        │
        ▼ (Interactions: Swaps / Inputs)
 [ Streamlit Interface UI ] ──(Reads State)──► [ Session State Machine ]
        │                                               │
        ▼ (If Cache Expired / 30m)                     ▼ (Triggers)
 [ Memory Cache Logic ] ◄───────────────────────── [ Math Engine ]
        │                                        (Triangular Conversion)
        ▼ 
 [ Live Exchange Rate API ]
