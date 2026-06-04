import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import json

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Smart Supply Platform PoC",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Secure Web API Connection Layer ---
supabase: Client = None
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    try:
        # Initialize the native web client using API key
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        st.sidebar.success("⚡ Supabase API Connected")
    except Exception as e:
        st.sidebar.error("🔌 Supabase Connection Failed")
        st.sidebar.caption(f"Error details: {e}")
else:
    st.sidebar.warning("⚠️ API credentials missing from Secrets.")

# --- 3. Mock Supplier API Data ---
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
                mock_ai_extracted_json = {
                    "items": [
                        {"name": "cement", "quantity": 50},
                        {"name": "drywall", "quantity": 15}
                    ],
                    "target_delivery": "2026-06-12"
                }
                
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
                    
                    if items_matched == len(req_items):
                        compiled_offers.append({
                            "supplier": supplier,
                            "total_cost": total_supplier_cost,
                            "delivery_date": target_date,
                            "metadata_payload": json.dumps(breakdown)
                        })
                
                if compiled_offers:
                    df_offers = pd.DataFrame(compiled_offers)
                    df_offers = df_offers.sort_values(by="total_cost").reset_index(drop=True)
                    
                    st.subheader("Available Market Options")
                    st.dataframe(
                        df_offers[["supplier", "total_cost", "delivery_date"]], 
                        use_container_width=True
                    )
                    
                    st.session_state['pending_order'] = df_offers.iloc[0].to_dict()
                else:
                    st.error("No single supplier has complete stock matching your exact requirements.")

    # Checkout Engine
    if 'pending_order' in st.session_state:
        st.write("---")
        st.subheader("Confirm Best Value Allocation")
        best_deal = st.session_state['pending_order']
        st.write(f"Proceed with **{best_deal['supplier']}** for a total of **£{best_deal['total_cost']:,.2f}**?")
        
        if st.button("Confirm and Route Order"):
            if supabase:
                try:
                    # Insert data via the web API client instead of raw SQL
                    data, count = supabase.table("order_logs").insert({
                        "supplier": best_deal["supplier"],
                        "total_cost": float(best_deal["total_cost"]),
                        "delivery_date": best_deal["delivery_date"],
                        "metadata_payload": best_deal["metadata_payload"]
                    }).execute()
                    
                    st.success("✅ Order successfully committed to operational stack and logged to Data Lake!")
                    del st.session_state['pending_order']
                    st.balloons()
                except Exception as db_err:
                    st.error(f"Failed to log record via Supabase API: {db_err}")
            else:
                st.error("Supabase API Client uninitialized. Cannot write transaction log.")


# VIEW B: OPERATIONS & ANALYTICS
elif role == "📊 Operations & Analytics":
    st.title("📊 Market Intelligence & Operations Dashboard")
    st.markdown("This interface queries raw log layers stored inside your Supabase repository via API endpoint streams.")
    
    analytics_loaded = False
    if supabase:
        try:
            # Pull records via API Client response payload
            response = supabase.table("order_logs").select("*").order("created_at", desc=True).limit(500).execute()
            if response.data:
                df_analytics = pd.DataFrame(response.data)
                df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])
                analytics_loaded = True
        except Exception:
            st.sidebar.info("💡 Real table logs unavailable. Showing visualization blueprint.")
            
    if not analytics_loaded:
        # Fallback simulation data
        df_analytics = pd.DataFrame([
            {"created_at": "2026-06-01 09:00:00", "supplier": "Supplier Alpha", "total_cost": 525.00, "delivery_date": "2026-06-12"},
            {"created_at": "2026-06-02 11:30:00", "supplier": "Supplier Beta", "total_cost": 738.00, "delivery_date": "2026-06-12"},
            {"created_at": "2026-06-03 14:15:00", "supplier": "Supplier Alpha", "total_cost": 1050.00, "delivery_date": "2026-06-15"},
            {"created_at": "2026-06-04 10:00:00", "supplier": "Supplier Gamma", "total_cost": 298.50, "delivery_date": "2026-06-19"},
            {"created_at": "2026-06-04 15:45:00", "supplier": "Supplier Beta", "total_cost": 640.00, "delivery_date": "2026-06-20"}
        ])
        df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])

    # --- TRANSFORMATION LAYER ---
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