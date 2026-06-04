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
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        st.sidebar.success("⚡ Supabase API Connected")
    except Exception as e:
        st.sidebar.error("🔌 Supabase Connection Failed")
        st.sidebar.caption(f"Error details: {e}")
else:
    st.sidebar.warning("⚠️ API credentials missing from Secrets.")

# --- 3. Identity, Registration & Authentication Layer ---
st.sidebar.title("🔐 Access Control")

if "customer_id" not in st.session_state:
    st.session_state["customer_id"] = None

if "current_view" not in st.session_state:
    st.session_state["current_view"] = "👤 Customer Portal"

if not st.session_state["customer_id"]:
    auth_mode = st.sidebar.radio("Choose Action:", ["Sign In", "Sign Up / Register"])
    
    if auth_mode == "Sign In":
        st.sidebar.markdown("### Existing Client Login")
        login_id = st.sidebar.text_input("Enter Customer ID:", placeholder="e.g., CUST-101").strip()
        
        if st.sidebar.button("Log In", type="primary"):
            if not login_id:
                st.sidebar.error("Please enter your Customer ID.")
            elif supabase:
                try:
                    user_check = supabase.table("customers").select("*").eq("customer_id", login_id).execute()
                    if user_check.data and len(user_check.data) > 0:
                        st.session_state["customer_id"] = login_id
                        st.session_state["current_view"] = "👤 Customer Portal"
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Customer ID not found. Please register first.")
                except Exception as err:
                    st.sidebar.error(f"Authentication engine failure: {err}")
                    
    elif auth_mode == "Sign Up / Register":
        st.sidebar.markdown("### Create Partner Account")
        new_id = st.sidebar.text_input("Choose a Customer ID:", placeholder="e.g., BUILD-01").strip()
        new_company = st.sidebar.text_input("Company Legal Name:", placeholder="e.g., ACME Construction Ltd").strip()
        new_email = st.sidebar.text_input("Contact Email Address:", placeholder="e.g., procurement@acme.com").strip()
        
        if st.sidebar.button("Register Account", type="primary"):
            if not (new_id and new_company and new_email):
                st.sidebar.error("All registration fields are required.")
            elif supabase:
                try:
                    duplicate_check = supabase.table("customers").select("*").eq("customer_id", new_id).execute()
                    if duplicate_check.data and len(duplicate_check.data) > 0:
                        st.sidebar.error("⚠️ This Customer ID is already taken. Try another.")
                    else:
                        reg_response = supabase.table("customers").insert({
                            "customer_id": new_id,
                            "company_name": new_company,
                            "contact_email": new_email
                        }).execute()
                        
                        st.sidebar.success("🎉 Registration complete! Switch to 'Sign In' to log into your workspace.")
                except Exception as err:
                    st.sidebar.error(f"Failed to submit credentials: {err}")
else:
    st.sidebar.success(f"Active Session: **{st.session_state['customer_id']}**")
    
    st.sidebar.title("Navigation")
    role = st.sidebar.radio(
        "Select Interface:", 
        ["👤 Customer Portal", "📊 My Orders & Analytics"],
        key="navigation_radio",
        index=0 if st.session_state["current_view"] == "👤 Customer Portal" else 1
    )
    st.session_state["current_view"] = role

    if st.sidebar.button("Log Out"):
        st.session_state["customer_id"] = None
        st.session_state["current_view"] = "👤 Customer Portal"
        if "pending_order" in st.session_state:
            del st.session_state["pending_order"]
        st.rerun()

# --- 4. Mock Supplier API Data ---
MOCK_SUPPLIERS = {
    "Supplier Alpha": {"cement": 10.50, "drywall": 15.00, "gravel": 32.00},
    "Supplier Beta": {"cement": 11.00, "drywall": 14.20, "gravel": 35.50},
    "Supplier Gamma": {"cement": 9.95, "drywall": 16.10, "gravel": 30.00}
}

# --- Helper Function to Clean JSON Metadata ---
def format_items_payload(payload_string):
    """Parses raw JSON string into a clean bulleted list with manual line breaks."""
    try:
        if not payload_string:
            return "No items logged"
        
        data_dict = json.loads(payload_string)
        # Format keys with clean spacing to respect newlines inside the text box cell
        formatted_lines = [f"• {item.title()}: {details}" for item, details in data_dict.items()]
        return "\n".join(formatted_lines)
    except Exception:
        return str(payload_string)

# --- 5. Application Routing Views ---
if not st.session_state["customer_id"]:
    st.title("📦 Smart Supply Platform")
    st.warning("🔒 Access Restricted. Please register an account or log in via the sidebar access panel to manage orders.")
else:
    # VIEW A: CUSTOMER PORTAL
    if st.session_state["current_view"] == "👤 Customer Portal":
        st.title(f"📦 Smart Procurement Portal")
        st.caption(f"Acting on behalf of tenant: {st.session_state['customer_id']}")
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
                    mock_ai_extracted_json = {
                        "items": [
                            {"name": "cement", "quantity": 50},
                            {"name": "drywall", "quantity": 15}
                        ],
                        "target_delivery": "2026-06-12"
                    }
                    st.info("💡 **AI Extraction Success:** Unstructured request parsed into standard data models.")
                    
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
                        st.dataframe(df_offers[["supplier", "total_cost", "delivery_date"]], use_container_width=True)
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
                        data, count = supabase.table("order_logs").insert({
                            "customer_id": st.session_state["customer_id"],
                            "supplier": best_deal["supplier"],
                            "total_cost": float(best_deal["total_cost"]),
                            "delivery_date": best_deal["delivery_date"],
                            "metadata_payload": best_deal["metadata_payload"]
                        }).execute()
                        
                        st.success("✅ Order successfully committed and partitioned to your Customer ID!")
                        st.balloons()
                        
                        del st.session_state['pending_order']
                        if st.button("📋 Go to My Orders Ledger"):
                            st.session_state["current_view"] = "📊 My Orders & Analytics"
                            st.rerun()
                            
                    except Exception as db_err:
                        st.error(f"Failed to log record via Supabase API: {db_err}")
                else:
                    st.error("Supabase API Client uninitialized. Cannot write transaction log.")

    # VIEW B: USER SPECIFIC ORDERS & ANALYTICS
    elif st.session_state["current_view"] == "📊 My Orders & Analytics":
        st.title("📊 Personal Procurement Dashboard")
        st.markdown(f"Displaying historical procurement flows and analytics exclusively for: **{st.session_state['customer_id']}**")
        
        analytics_loaded = False
        if supabase:
            try:
                response = supabase.table("order_logs")\
                                   .select("*")\
                                   .eq("customer_id", st.session_state["customer_id"])\
                                   .order("created_at", desc=True)\
                                   .execute()
                
                if response.data and len(response.data) > 0:
                    df_analytics = pd.DataFrame(response.data)
                    df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])
                    analytics_loaded = True
                else:
                    st.info("ℹ️ No historical orders found for this Customer ID yet. Place an order to generate real-time metrics.")
            except Exception as err:
                st.sidebar.error(f"Failed to pull active stream: {err}")
                
        if not analytics_loaded:
            st.markdown("### Prototype Template Preview (No Real Orders Yet)")
            df_analytics = pd.DataFrame([
                {"created_at": "2026-06-04 12:00:00", "supplier": "Supplier Alpha", "total_cost": 0.0, "delivery_date": "2026-06-12", "customer_id": st.session_state["customer_id"], "metadata_payload": "{}"}
            ])
            df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])

        # --- DATA CLEANING LAYER ---
        # 1. Format the items into strings with raw newlines
        df_analytics["Items"] = df_analytics["metadata_payload"].apply(format_items_payload)
        
        # 2. Extract and format a dedicated, clean customer-facing Order Date
        df_analytics["Order Date"] = df_analytics["created_at"].dt.strftime("%d %b %Y, %H:%M")
        
        # 3. Rename metric headers cleanly
        df_analytics = df_analytics.rename(columns={
            "supplier": "Allocated Supplier",
            "total_cost": "Total Spend (£)",
            "delivery_date": "Est. Delivery Date"
        })

        # --- VISUALIZATION LAYER ---
        if analytics_loaded:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Your Spend Velocity")
                fig_line = px.line(
                    df_analytics, 
                    x="Order Date", 
                    y="Total Spend (£)", 
                    color="Allocated Supplier",
                    title="Order Allocation Streams",
                    labels={"Total Spend (£)": "Cost (£)"},
                    markers=True
                )
                st.plotly_chart(fig_line, use_container_width=True)
                
            with col2:
                st.markdown("#### Vendor Allocation Share")
                fig_pie = px.pie(
                    df_analytics, 
                    names="Allocated Supplier", 
                    values="Total Spend (£)", 
                    title="Where Your Orders Are Routed"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("Your Order History Ledger")
            
            # Filter layout to ONLY include the columns the customer needs to see
            display_cols = [
                "Order Date", 
                "Allocated Supplier", 
                "Items", 
                "Total Spend (£)", 
                "Est. Delivery Date"
            ]
            
            # --- UI RENDERING CONFIGURATION ---
            st.dataframe(
                df_analytics[display_cols], 
                use_container_width=True,
                hide_index=True,  # <--- Removes the unlabelled left-most sequential index column entirely
                column_config={
                    "Items": st.column_config.TextColumn(
                        "Items",
                        help="Structured item details parsed from unstructured request",
                        width="large"  # Expands the container box so multi-line text reads beautifully
                    )
                }
            )