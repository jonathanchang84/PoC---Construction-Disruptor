import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import json

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Smart Supply Platform PoC",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Secure Database Connection Layer ---
engine = None
if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
    db_url = st.secrets["connections"]["url"]
    
    # Fix standard dialect naming quirk for SQLAlchemy if needed
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    try:
        # Initialize standard engine with pre-ping validation
        engine = create_engine(db_url, pool_pre_ping=True)
        # Quick health check test
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        st.sidebar.success("🔌 Supabase Connected")
    except Exception as e:
        st.sidebar.error("🔌 Supabase Connection Failed")
        st.sidebar.caption(f"Error details: {e}")
else:
    st.sidebar.warning("⚠️ Database credentials missing from Secrets.")

# --- 3. Mock Supplier API Data ---
# In production, these would be direct API calls fetching live vendor details
MOCK_SUPPLIERS = {
    "Supplier Alpha": {"cement": 10.50, "drywall": 15.00, "gravel": 32.00},
    "Supplier Beta": {"cement": 11.00, "drywall": 14.20, "gravel": 35.50},
    "Supplier Gamma": {"cement": 9.95, "drywall": 16.10, "gravel": 30.00}
}

# --- 4. Navigation & Architecture ---
st.sidebar.title("Navigation")
role = st.sidebar.radio("Select Interface:", ["👤 Customer Portal", "📊 Operations & Analytics"])

# --- 5. Application Views ---

# VIEW A: CUSTOMER PORTAL
if role == "👤 Customer Portal":
    st.title("📦 Smart Procurement Portal")
    st.markdown("Submit your material requests naturally. Our AI engine will structure the requirements and match live vendor availability.")
    
    st.subheader("What do you need today?")
    user_input = st.text_area(
        "Enter project requirements:",
        placeholder="e.g., I'm looking for 50 bags of cement and 15 sheets of drywall by next Friday...",
        height=120
    )
    
    if st.button("Process Request with AI", type="primary"):
        if not user_input.strip():
            st.error("Please enter a description first.")
        else:
            with st.spinner("Analyzing text and evaluating market inventory..."):
                # --- AI INTERPRETER FRAMEWORK ---
                # This simulates the structural output pattern you will establish with Gemini.
                # Gemini will take unstructured prose and reliably return a predictable JSON payload.
                
                # Mocked parsing result for prototyping the pipeline
                mock_ai_extracted_json = {
                    "items": [
                        {"name": "cement", "quantity": 50},
                        {"name": "drywall", "quantity": 15}
                    ],
                    "target_delivery": "2026-06-12"
                }
                
                # Visual verification for the user/admin
                st.info("💡 **AI Extraction Success:** Unstructured request parsed into standard data models.")
                
                # --- SUPPLIER MATCHING ENGINE ---
                compiled_offers = []
                req_items = mock_ai_extracted_json["items"]
                target_date = mock_ai_extracted_json["target_delivery"]
                
                for supplier, inventory in MOCK_SUPPLIERS.items():
                    total_supplier_cost = 0.0
                    items_matched = 0
                    breakdown = {}
                    
                    for item in req_items:
                        item_name = item["name"].lower()
                        qty = item["quantity"]
                        
                        if item_name in inventory:
                            unit_price = inventory[item_name]
                            line_cost = unit_price * qty
                            total_supplier_cost += line_cost
                            items_matched += 1
                            breakdown[item_name] = f"{qty} x £{unit_price:,.2f}"
                    
                    # Only show vendors capable of fulfilling all requested materials
                    if items_matched == len(req_items):
                        compiled_offers.append({
                            "Supplier": supplier,
                            "Total Fulfillment Cost": total_supplier_cost,
                            "Fulfillment Date": target_date,
                            "Breakdown Details": json.dumps(breakdown)
                        })
                
                if compiled_offers:
                    df_offers = pd.DataFrame(compiled_offers)
                    # Sort options to highlight the best market value first
                    df_offers = df_offers.sort_values(by="Total Fulfillment Cost").reset_index(drop=True)
                    
                    st.subheader("Available Market Options")
                    st.dataframe(
                        df_offers[["Supplier", "Total Fulfillment Cost", "Fulfillment Date"]], 
                        use_container_width=True
                    )
                    
                    # Store session state for checkout persistence
                    st.session_state['pending_order'] = df_offers.iloc[0].to_dict()
                else:
                    st.error("No single supplier has complete stock matching your exact requirements.")

    # Checkout Engine
    if 'pending_order' in st.session_state:
        st.write("---")
        st.subheader("Confirm Best Value Allocation")
        best_deal = st.session_state['pending_order']
        st.write(f"Proceed with **{best_deal['Supplier']}** for a total of **£{best_deal['Total Fulfillment Cost']:,.2f}**?")
        
        if st.button("Confirm and Route Order"):
            if engine:
                try:
                    with engine.connect() as connection:
                        # Writing structural data explicitly to the Data Lake
                        insert_query = text("""
                            INSERT INTO order_logs (supplier, total_cost, delivery_date, metadata_payload)
                            VALUES (:supplier, :cost, :delivery, :meta);
                        """)
                        connection.execute(insert_query, {
                            "supplier": best_deal["Supplier"],
                            "cost": float(best_deal["Total Fulfillment Cost"]),
                            "delivery": best_deal["Fulfillment Date"],
                            "meta": best_deal["Breakdown Details"]
                        })
                        connection.commit()
                    st.success("✅ Order successfully committed to operational stack and logged to Data Lake!")
                    del st.session_state['pending_order']
                    st.balloons()
                except Exception as db_err:
                    st.error(f"Failed to log record to Supabase: {db_err}")
            else:
                st.error("Database engine uninitialized. Cannot write transaction log.")


# VIEW B: OPERATIONS & ANALYTICS
elif role == "📊 Operations & Analytics":
    st.title("📊 Market Intelligence & Operations Dashboard")
    st.markdown("This interface queries raw log layers stored inside your Supabase repository, showcasing data aggregation monetization potential.")
    
    # Check if database pipeline is live, fall back to safe mock analytics if table doesn't exist yet
    analytics_loaded = False
    if engine:
        try:
            with engine.connect() as connection:
                query = "SELECT * FROM order_logs ORDER BY created_at DESC LIMIT 500;"
                df_analytics = pd.read_sql(query, con=engine)
                analytics_loaded = True
        except Exception:
            # Table may not exist yet in Supabase UI editor
            st.sidebar.info("💡 Table 'order_logs' not found. Displaying prototype analytics stream.")
            
    if not analytics_loaded:
        # Standard structural template for monetization presentation layer
        df_analytics = pd.DataFrame([
            {"created_at": "2026-06-01 09:00:00", "supplier": "Supplier Alpha", "total_cost": 525.00, "delivery_date": "2026-06-12", "item_class": "Cement"},
            {"created_at": "2026-06-02 11:30:00", "supplier": "Supplier Beta", "total_cost": 738.00, "delivery_date": "2026-06-12", "item_class": "Drywall"},
            {"created_at": "2026-06-03 14:15:00", "supplier": "Supplier Alpha", "total_cost": 1050.00, "delivery_date": "2026-06-15", "item_class": "Cement"},
            {"created_at": "2026-06-04 10:00:00", "supplier": "Supplier Gamma", "total_cost": 298.50, "delivery_date": "2026-06-19", "item_class": "Gravel"},
            {"created_at": "2026-06-04 15:45:00", "supplier": "Supplier Beta", "total_cost": 640.00, "delivery_date": "2026-06-20", "item_class": "Drywall"}
        ])
        df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])

    # --- IN-MEMORY TRANSFORMATION LAYER ---
    st.subheader("Data Optimization Filter")
    selected_vendor = st.selectbox("Filter Metrics By Executing Vendor:", ["All Vendors"] + list(df_analytics["supplier"].unique()))
    
    filtered_df = df_analytics if selected_vendor == "All Vendors" else df_analytics[df_analytics["supplier"] == selected_vendor]
    
    # --- VISUALIZATION LAYER ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Transaction Volumes Over Time")
        fig_line = px.line(
            filtered_df, 
            x="created_at", 
            y="total_cost", 
            color="supplier" if selected_vendor == "All Vendors" else None,
            title="Order Velocity & Capture Rates",
            labels={"created_at": "Log Timestamp", "total_cost": "Value (£)"},
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col2:
        st.markdown("#### Market Capture Share")
        fig_pie = px.pie(
            filtered_df, 
            names="supplier", 
            values="total_cost", 
            title="Order Allocation Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Raw Storage Lake Audit Stream")
    st.dataframe(filtered_df, use_container_width=True)