import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import json
import re
import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Smart Supply Platform PoC",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Secure Web API Connection Layer (Supabase & Gemini) ---
supabase: Client = None
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    try:
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        st.sidebar.success("⚡ Supabase API Connected")
    except Exception as e:
        st.sidebar.error("🔌 Supabase Connection Failed")
        st.sidebar.caption(f"Error details: {e}")
else:
    st.sidebar.warning("⚠️ Supabase credentials missing from Secrets.")

gemini_ready = False
if "GEMINI_API_KEY" in st.secrets:
    gemini_ready = True
    st.sidebar.success("🤖 Gemini AI Engine Initialized")
else:
    st.sidebar.error("❌ GEMINI_API_KEY missing from Secrets.")

# --- 3. Structured Data Models for Estimations ---
class MaterialItem(BaseModel):
    name: str = Field(description="The exact material name or its closest matched equivalent from the provided catalog list.")
    quantity: int = Field(description="The final total count or volume of items calculated to fulfill the request.")
    reasoning_breakdown: str = Field(description="A brief, 1-sentence math breakdown explaining exactly how this quantity was derived from structural measurements.")

class ProcurementIntent(BaseModel):
    items: list[MaterialItem] = Field(description="A collection of structured items parsed and calculated from the text.")

# --- 4. Identity & Authentication Layer ---
st.sidebar.title("🔐 Access Control")

# Initialize persistent tracking keys if absent
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None  # Tracks 'customer' vs 'operations'
if "current_view" not in st.session_state:
    st.session_state["current_view"] = None

if not st.session_state["user_id"]:
    # Dual-profile entry gateway
    login_profile = st.sidebar.radio("Select Portal Profile:", ["👤 Client Partner", "⚙️ Internal Operations"])
    
    if login_profile == "👤 Client Partner":
        auth_mode = st.sidebar.selectbox("Choose Action:", ["Sign In", "Sign Up / Register"])
        
        if auth_mode == "Sign In":
            st.sidebar.markdown("### Existing Client Login")
            login_id = st.sidebar.text_input("Enter Customer ID:", placeholder="e.g., CUST-101").strip()
            
            if st.sidebar.button("Log In as Client", type="primary"):
                if not login_id:
                    st.sidebar.error("Please enter your Customer ID.")
                elif supabase:
                    try:
                        user_check = supabase.table("customers").select("*").eq("customer_id", login_id).execute()
                        if user_check.data and len(user_check.data) > 0:
                            st.session_state["user_id"] = login_id
                            st.session_state["user_role"] = "customer"
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
                            supabase.table("customers").insert({
                                "customer_id": new_id,
                                "company_name": new_company,
                                "contact_email": new_email
                            }).execute()
                            st.sidebar.success("🎉 Registration complete! Switch to 'Sign In' to log into your workspace.")
                    except Exception as err:
                        st.sidebar.error(f"Failed to submit credentials: {err}")
                        
    elif login_profile == "⚙️ Internal Operations":
        st.sidebar.markdown("### Operations Control Login")
        ops_user_id = st.sidebar.text_input("Enter Operator Badge ID:", placeholder="e.g., OPS-09").strip()
        
        if st.sidebar.button("Verify & Open Console", type="primary"):
            if not ops_user_id:
                st.sidebar.error("Please input an authorized Operator ID.")
            else:
                # For PoC testing purposes, allows entry and tracks ID. 
                # (Can easily map to an 'operations_team' table in Supabase later)
                st.session_state["user_id"] = ops_user_id
                st.session_state["user_role"] = "operations"
                st.session_state["current_view"] = "📋 Order Overview"
                st.rerun()
else:
    # --- Authenticated User Layout Customization Matrix ---
    st.sidebar.success(f"Session: **{st.session_state['user_id']}** ({st.session_state['user_role'].upper()})")
    st.sidebar.title("Navigation")
    
    # Restrict interface visualization mapping vectors dynamically based on security role
    if st.session_state["user_role"] == "operations":
        view_options = ["📋 Order Overview"]
    else:
        view_options = ["👤 Customer Portal", "📊 My Orders & Analytics"]
        
    current_idx = 0
    if st.session_state["current_view"] in view_options:
        current_idx = view_options.index(st.session_state["current_view"])
        
    role = st.sidebar.radio(
        "Select Interface:", 
        view_options,
        key="navigation_radio",
        index=current_idx
    )
    st.session_state["current_view"] = role

    if st.sidebar.button("Log Out and Disconnect"):
        st.session_state["user_id"] = None
        st.session_state["user_role"] = None
        st.session_state["current_view"] = None
        if "pending_order" in st.session_state:
            del st.session_state["pending_order"]
        st.rerun()

# --- Helper Function to Clean JSON Metadata ---
def format_items_payload_html(payload_string):
    try:
        if not payload_string:
            return "No items logged"
        data_dict = json.loads(payload_string)
        formatted_lines = [f"• {item.title()}: {details}" for item, details in data_dict.items()]
        return "<br>".join(formatted_lines)
    except Exception:
        return str(payload_string)

# --- Helper Function to Render Styled Status Pills ---
def render_status_pill_html(status_string):
    status = str(status_string).strip()
    if status == "Order Placed":
        return f'<span style="background-color: #e1f5fe; color: #0288d1; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: bold; border: 1px solid #b3e5fc;">📋 {status}</span>'
    elif status == "Processing":
        return f'<span style="background-color: #fff8e1; color: #f57f17; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: bold; border: 1px solid #ffe082;">⚙️ {status}</span>'
    elif status == "On its way":
        return f'<span style="background-color: #e8f5e9; color: #388e3c; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: bold; border: 1px solid #c8e6c9;">🚚 {status}</span>'
    elif status == "Delivered":
        return f'<span style="background-color: #ede7f6; color: #5e35b1; padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: bold; border: 1px solid #d1c4e9;">✅ {status}</span>'
    else:
        return f'<span style="background-color: #f5f5f5; color: #616161; padding: 4px 10px; border-radius: 12px; font-size: 13px;">{status}</span>'

# --- 5. Application Routing Views ---
if not st.session_state["user_id"]:
    st.title("📦 Smart Supply Platform")
    st.warning("🔒 Access Restricted. Please log in via the sidebar access panel to manage order streams.")
else:
    # -------------------------------------------------------------
    # VIEW A: CUSTOMER PORTAL
    # -------------------------------------------------------------
    if st.session_state["current_view"] == "👤 Customer Portal":
        st.title(f"📦 Smart Procurement Portal")
        st.caption(f"Acting on behalf of tenant: {st.session_state['user_id']}")
        st.markdown("Submit your material requests naturally. Our Gemini AI engine will structure the requirements and match live vendor availability.")
        
        with st.expander("📖 View Active Material Catalog (Soft-Coded from Supabase)"):
            if supabase:
                try:
                    inv_data = supabase.table("supplier_inventory").select("item_name, unit_price").execute()
                    if inv_data.data:
                        unique_items = pd.DataFrame(inv_data.data).drop_duplicates().reset_index(drop=True)
                        unique_items.columns = ["Available Material", "Market Base Price"]
                        st.dataframe(unique_items, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.caption(f"Could not load catalog overview: {e}")
        
        st.subheader("What do you need today?")
        user_input = st.text_area(
            "Enter project requirements:",
            placeholder="e.g., I would like enough bricks to build the walls of a room 4mx5m...",
            height=120,
            key="customer_material_input"
        )
        
        if st.button("Process Request with AI", type="primary"):
            if not user_input.strip():
                st.error("Please enter a description first.")
            elif not supabase:
                st.error("Supabase connection missing.")
            elif not gemini_ready:
                st.error("Gemini client configuration missing. Check secrets setup.")
            else:
                with st.spinner("Invoking Gemini 2.5 Flash Estimation Engine..."):
                    try:
                        db_query = supabase.table("supplier_inventory").select("supplier_name, item_name, unit_price").execute()
                        if not db_query.data:
                            st.error("The supplier inventory table is empty.")
                            st.stop()
                            
                        dynamic_suppliers = {}
                        for row in db_query.data:
                            sup = row['supplier_name']
                            item = row['item_name']
                            price = float(row['unit_price'])
                            if sup not in dynamic_suppliers:
                                dynamic_suppliers[sup] = {}
                            dynamic_suppliers[sup][item] = price
                            
                        known_db_items = list(set([row['item_name'] for row in db_query.data]))
                        
                        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                        system_context_prompt = f"""
                        You are an expert construction estimator and logistics parsing engine.
                        Your task is to convert conversational or architectural requests into exact material counts.
                        Available System Catalog Items: {known_db_items}
                        
                        Rules for Structural Estimation:
                        1. If the user asks for 'bricks' or related materials to build walls for a room layout but doesn't specify height, assume a standard room ceiling height of 2.4 meters.
                        2. Use the industry standard calculation formula: A single-skin brick wall requires exactly 60 bricks per square meter.
                        3. Always calculate the total wall perimeter (sum of all 4 sides), multiply by height to get total area, multiply by 60, and then append a 10% safety/wastage margin. Round up to the nearest integer.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=f"Process requirements string: {user_input}",
                            config=types.GenerateContentConfig(
                                system_instruction=system_context_prompt,
                                response_mime_type="application/json",
                                response_schema=ProcurementIntent,
                                temperature=0.1
                            ),
                        )
                        
                        llm_payload = json.loads(response.text)
                        mock_ai_extracted_json = {"items": llm_payload.get("items", []), "target_delivery": "2026-06-12"}
                        
                        st.info("💡 **Gemini Extraction & Engineering Engine Success:**")
                        for calc_item in mock_ai_extracted_json["items"]:
                            with st.container():
                                col_b1, col_b2 = st.columns([1, 4])
                                col_b1.metric(label=f"Calculated {calc_item['name'].title()}", value=f"{calc_item['quantity']:,}")
                                col_b2.markdown(f"**AI Engineering Estimation Breakdown:**\n*{calc_item['reasoning_breakdown']}*")
                        
                        compiled_offers = []
                        req_items = mock_ai_extracted_json["items"]
                        target_date = mock_ai_extracted_json["target_delivery"]
                        
                        for supplier, inventory in dynamic_suppliers.items():
                            total_supplier_cost = 0.0
                            breakdown = {}
                            for item in req_items:
                                item_name = item["name"].lower().strip()
                                qty = item["quantity"]
                                if item_name in inventory:
                                    unit_price = inventory[item_name]
                                    total_supplier_cost += unit_price * qty
                                    breakdown[item_name] = f"{qty} x £{unit_price:,.2f}"
                                else:
                                    proxy_price = 10.00
                                    total_supplier_cost += proxy_price * qty
                                    breakdown[item_name] = f"{qty} x £{proxy_price:,.2f} (Special Order)"
                            
                            compiled_offers.append({
                                "supplier": supplier,
                                "total_cost": total_supplier_cost,
                                "delivery_date": target_date,
                                "metadata_payload": json.dumps(breakdown)
                            })
                        
                        if compiled_offers:
                            df_offers = pd.DataFrame(compiled_offers).sort_values(by="total_cost").reset_index(drop=True)
                            st.subheader("Available Market Options")
                            st.dataframe(df_offers[["supplier", "total_cost", "delivery_date"]], use_container_width=True)
                            st.session_state['pending_order'] = df_offers.iloc[0].to_dict()
                            
                    except Exception as pipeline_error:
                        st.error(f"Gemini estimation processing loop failed: {pipeline_error}")

        if 'pending_order' in st.session_state:
            st.write("---")
            st.subheader("Confirm Best Value Allocation")
            best_deal = st.session_state['pending_order']
            st.write(f"Proceed with **{best_deal['supplier']}** for a total of **£{best_deal['total_cost']:,.2f}**?")
            
            if st.button("Confirm and Route Order"):
                if supabase:
                    try:
                        max_seq_check = supabase.table("order_logs_scd").select("order_no").order("order_no", desc=True).limit(1).execute()
                        next_order_no = 1001
                        if max_seq_check.data and len(max_seq_check.data) > 0:
                            next_order_no = int(max_seq_check.data[0]["order_no"]) + 1
                        
                        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        
                        supabase.table("order_logs_scd").insert({
                            "order_no": next_order_no,
                            "customer_id": st.session_state["user_id"],
                            "supplier": best_deal["supplier"],
                            "total_cost": float(best_deal["total_cost"]),
                            "delivery_date": best_deal["delivery_date"],
                            "metadata_payload": best_deal["metadata_payload"],
                            "status": "Order Placed",
                            "valid_from": now_iso,
                            "is_current": True,
                            "modified_by": st.session_state["user_id"]
                        }).execute()
                        
                        st.success(f"✅ Order #{next_order_no} committed successfully!")
                        del st.session_state['pending_order']
                        st.balloons()
                        st.session_state["current_view"] = "📊 My Orders & Analytics"
                        st.rerun()
                    except Exception as db_err:
                        st.error(f"Failed to submit log row: {db_err}")

    # -------------------------------------------------------------
    # VIEW B: CUSTOMER SPECIFIC ORDERS & ANALYTICS
    # -------------------------------------------------------------
    elif st.session_state["current_view"] == "📊 My Orders & Analytics":
        st.title("📊 Personal Procurement Dashboard")
        st.markdown(f"Displaying historical procurement flows for tenant: **{st.session_state['user_id']}**")
        
        analytics_loaded = False
        if supabase:
            try:
                response = supabase.table("order_logs_scd").select("*").eq("customer_id", st.session_state["user_id"]).eq("is_current", True).order("valid_from", desc=True).execute()
                if response.data and len(response.data) > 0:
                    df_analytics = pd.DataFrame(response.data)
                    df_analytics["created_at"] = pd.to_datetime(df_analytics["valid_from"])
                    analytics_loaded = True
                else:
                    st.info("ℹ️ No historical active orders found.")
            except Exception as err:
                st.sidebar.error(f"Failed to pull active stream: {err}")
                
        if not analytics_loaded:
            df_analytics = pd.DataFrame([
                {"order_no": 1001, "valid_from": "2026-06-04T12:00:00Z", "supplier": "Supplier Alpha", "total_cost": 0.0, "delivery_date": "2026-06-12", "customer_id": st.session_state["user_id"], "metadata_payload": "{}", "status": "Order Placed"}
            ])
            df_analytics["created_at"] = pd.to_datetime(df_analytics["valid_from"])

        df_analytics["Items"] = df_analytics["metadata_payload"].apply(format_items_payload_html)
        df_analytics["Order Date"] = df_analytics["created_at"].dt.strftime("%d %b %Y, %H:%M")
        df_analytics["Tracking Status"] = df_analytics["status"].apply(render_status_pill_html)
        
        df_analytics = df_analytics.rename(columns={"order_no": "Order No.", "supplier": "Allocated Supplier", "total_cost": "Total Spend", "delivery_date": "Est. Delivery Date"})

        if analytics_loaded:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.line(df_analytics, x="Order Date", y="Total Spend", color="Allocated Supplier", title="Order Spend Velocity", markers=True), use_container_width=True)
            with col2:
                st.plotly_chart(px.pie(df_analytics, names="Allocated Supplier", values="Total Spend", title="Vendor Share Allocation"), use_container_width=True)

            st.subheader("Your Order History Ledger")
            df_display = df_analytics[["Order No.", "Order Date", "Allocated Supplier", "Items", "Total Spend", "Est. Delivery Date", "Tracking Status"]].copy()
            df_display["Total Spend"] = df_display["Total Spend"].apply(lambda x: f"£{x:,.2f}" if isinstance(x, (int, float)) else x)
            
            st.markdown(
                """
                <style>
                .custom-ledger-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-family: sans-serif; }
                .custom-ledger-table th { background-color: #f0f2f6; color: #31333F; text-align: left; padding: 12px; border-bottom: 2px solid #e6e8f1; }
                .custom-ledger-table td { padding: 12px; border-bottom: 1px solid #e6e8f1; vertical-align: top; }
                </style>
                """, unsafe_allow_html=True
            )
            st.markdown(df_display.to_html(index=False, escape=False, classes="custom-ledger-table"), unsafe_allow_html=True)

    # -------------------------------------------------------------
    # VIEW C: ORDER OVERVIEW INTERFACE (Internal Operations Hub)
    # -------------------------------------------------------------
    elif st.session_state["current_view"] == "📋 Order Overview":
        st.title("📋 Master Order Overview Console")
        st.markdown("Global administration cockpit. Displaying currently active operational tracking states across all network client tenants.")
        
        if supabase:
            try:
                global_query = supabase.table("order_logs_scd").select("*").eq("is_current", True).order("valid_from", desc=True).execute()
                
                if global_query.data:
                    df_global = pd.DataFrame(global_query.data)
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Global Gross Routed Volumes", f"£{df_global['total_cost'].sum():,.2f}")
                    m2.metric("Total Platform Transactions", len(df_global))
                    m3.metric("Unique Customer Entities Active", df_global['customer_id'].nunique())
                    
                    st.write("---")
                    st.subheader("Global Order Fulfillment Audit Stream")
                    
                    df_global["Status Tracker"] = df_global["status"].apply(render_status_pill_html)
                    df_global["Items Requested"] = df_global["metadata_payload"].apply(format_items_payload_html)
                    df_global["Timestamp"] = pd.to_datetime(df_global["valid_from"]).dt.strftime("%Y-%m-%d %H:%M")
                    
                    admin_display_cols = ["order_no", "Timestamp", "customer_id", "supplier", "Items Requested", "total_cost", "delivery_date", "Status Tracker", "modified_by"]
                    df_admin_view = df_global[admin_display_cols].copy()
                    df_admin_view.columns = ["Order No", "Last Updated", "Client ID", "Fulfillment Supplier", "Items Extracted", "Total Valuation", "Est Delivery Target", "Current Status", "Last Modified By"]
                    
                    st.markdown(df_admin_view.to_html(index=False, escape=False, classes="custom-ledger-table"), unsafe_allow_html=True)
                    
                    # Administration interactive state engine modifier block
                    st.write("---")
                    st.subheader("🛠️ Operations Fulfillment Control (SCD Type 2 Audit Logging)")
                    st.markdown("Updating status fields here will expire the active tracking record and append a fresh historical row log.")
                    
                    col_adm1, col_adm2, col_adm3 = st.columns(3)
                    target_order_no = col_adm1.selectbox("Select Target Order No:", options=df_global["order_no"].unique().tolist())
                    target_new_status = col_adm2.selectbox("Set Next Lifecycle State:", options=["Order Placed", "Processing", "On its way", "Delivered"])
                    
                    if col_adm3.button("Execute Status Update", type="primary", use_container_width=True):
                        try:
                            active_record = df_global[df_global["order_no"] == target_order_no].iloc[0]
                            now_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                            
                            # STEP A: Expire active visibility parameter flags
                            supabase.table("order_logs_scd").update({
                                "is_current": False,
                                "valid_to": now_timestamp
                            }).eq("order_no", int(target_order_no)).eq("is_current", True).execute()
                            
                            # STEP B: Insert updated status entry tracking execution user badge ID
                            supabase.table("order_logs_scd").insert({
                                "order_no": int(target_order_no),
                                "customer_id": str(active_record["customer_id"]),
                                "supplier": str(active_record["supplier"]),
                                "total_cost": float(active_record["total_cost"]),
                                "delivery_date": str(active_record["delivery_date"]),
                                "metadata_payload": str(active_record["metadata_payload"]),
                                "status": target_new_status,
                                "valid_from": now_timestamp,
                                "is_current": True,
                                "modified_by": st.session_state["user_id"] # Saves active Operator badge ID
                            }).execute()
                            
                            st.success(f"🎉 Order #{target_order_no} migrated to state '{target_new_status}'! Log appended.")
                            st.rerun()
                        except Exception as update_err:
                            st.error(f"Failed to execute SCD Type 2 update: {update_err}")
                else:
                    st.info("No system transaction histories logs present in Supabase order_logs_scd.")
            except Exception as e:
                st.error(f"Failed to extract global metrics logs from Supabase connection: {e}")
        else:
            st.error("Supabase API connection client layer uninitialized.")