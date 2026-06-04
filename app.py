import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import json
import re
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

# --- 3. Structured Data Models for LLM Enforcement ---
class MaterialItem(BaseModel):
    name: str = Field(description="The exact material name or its closest matched equivalent from the provided catalog list.")
    quantity: int = Field(description="The structural volume or number of units requested by the client.")

class ProcurementIntent(BaseModel):
    items: list[MaterialItem] = Field(description="A collection of structured items parsed from the unstructured text.")

# --- 4. Identity & Authentication Layer ---
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

# --- 5. Application Routing Views ---
if not st.session_state["customer_id"]:
    st.title("📦 Smart Supply Platform")
    st.warning("🔒 Access Restricted. Please log in via the sidebar access panel to manage orders.")
else:
    # VIEW A: CUSTOMER PORTAL
    if st.session_state["current_view"] == "👤 Customer Portal":
        st.title(f"📦 Smart Procurement Portal")
        st.caption(f"Acting on behalf of tenant: {st.session_state['customer_id']}")
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
            placeholder="e.g., I want nails, 500 of them, and send over around 30 sheets of drywall too...",
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
                with st.spinner("Invoking Gemini 2.5 Flash to parse semantic intent..."):
                    
                    try:
                        # Fetch the target product keywords from Supabase to inform Gemini
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
                        
                        # --- GENAI EXTRACTION FLOW ---
                        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                        
                        system_context_prompt = f"""
                        You are a construction logistics data extraction parser. Your task is to process user requirements and extract materials.
                        You must match user intents to these specific system catalog items if they are synonyms or semantic fits: {known_db_items}.
                        
                        Rules:
                        1. If the user uses a conversational phrase like "I want nails, 500 of them", resolve that to quantity: 500, item name: 'nails'.
                        2. If they type a synonym (e.g. 'timber sheets' instead of 'osb flooring sheets'), normalize it to the correct catalog term.
                        3. Be precise with quantities.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=f"Extract from this string: {user_input}",
                            config=types.GenerateContentConfig(
                                system_instruction=system_context_prompt,
                                response_mime_type="application/json",
                                response_schema=ProcurementIntent,
                                temperature=0.1
                            ),
                        )
                        
                        # Load validated json output back into app dictionary workflow
                        llm_payload = json.loads(response.text)
                        
                        mock_ai_extracted_json = {
                            "items": llm_payload.get("items", []),
                            "target_delivery": "2026-06-12"
                        }
                        
                        st.info("💡 **Gemini Extraction Success:** Context-aware semantic parse completed.")
                        st.json(mock_ai_extracted_json)
                        
                        # --- VENDOR MATCHING ENGINE ---
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
                                    line_cost = unit_price * qty
                                    total_supplier_cost += line_cost
                                    breakdown[item_name] = f"{qty} x £{unit_price:,.2f}"
                                else:
                                    proxy_price = 10.00
                                    line_cost = proxy_price * qty
                                    total_supplier_cost += line_cost
                                    breakdown[item_name] = f"{qty} x £{proxy_price:,.2f} (Special Order)"
                            
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
                            st.error("Could not construct allocation options.")
                            
                    except Exception as pipeline_error:
                        st.error(f"Gemini processing loop failed: {pipeline_error}")

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
                        
                        st.success("✅ Order successfully committed!")
                        del st.session_state['pending_order']
                        st.balloons()
                        
                        st.session_state["current_view"] = "📊 My Orders & Analytics"
                        st.rerun()
                            
                    except Exception as db_err:
                        st.error(f"Failed to log record via Supabase API: {db_err}")
                else:
                    st.error("Supabase API Client uninitialized.")

    # VIEW B: USER SPECIFIC ORDERS & ANALYTICS
    elif st.session_state["current_view"] == "📊 My Orders & Analytics":
        st.title("📊 Personal Procurement Dashboard")
        st.markdown(f"Displaying historical procurement flows and analytics exclusively for: **{st.session_state['customer_id']}**")
        
        analytics_loaded = False
        if supabase:
            try:
                response = supabase.table("order_logs").select("*").eq("customer_id", st.session_state["customer_id"]).order("created_at", desc=True).execute()
                
                if response.data and len(response.data) > 0:
                    df_analytics = pd.DataFrame(response.data)
                    df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])
                    analytics_loaded = True
                else:
                    st.info("ℹ️ No historical orders found.")
            except Exception as err:
                st.sidebar.error(f"Failed to pull active stream: {err}")
                
        if not analytics_loaded:
            st.markdown("### Prototype Template Preview")
            df_analytics = pd.DataFrame([
                {"id": 1001, "created_at": "2026-06-04 12:00:00", "supplier": "Supplier Alpha", "total_cost": 0.0, "delivery_date": "2026-06-12", "customer_id": st.session_state["customer_id"], "metadata_payload": "{}"}
            ])
            df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"])

        # --- DATA CLEANING LAYER ---
        df_analytics["Items"] = df_analytics["metadata_payload"].apply(format_items_payload_html)
        df_analytics["Order Date"] = df_analytics["created_at"].dt.strftime("%d %b %Y, %H:%M")
        
        df_analytics = df_analytics.rename(columns={
            "id": "Order No.",
            "supplier": "Allocated Supplier",
            "total_cost": "Total Spend",
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
                    y="Total Spend", 
                    color="Allocated Supplier",
                    title="Order Allocation Streams",
                    labels={"Total Spend": "Cost (£)"},
                    markers=True
                )
                st.plotly_chart(fig_line, use_container_width=True)
                
            with col2:
                st.markdown("#### Vendor Allocation Share")
                fig_pie = px.pie(
                    df_analytics, 
                    names="Allocated Supplier", 
                    values="Total Spend", 
                    title="Where Your Orders Are Routed"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("Your Order History Ledger")
            
            display_cols = [
                "Order No.",
                "Order Date", 
                "Allocated Supplier", 
                "Items", 
                "Total Spend", 
                "Est. Delivery Date"
            ]
            
            df_display = df_analytics[display_cols].copy()
            df_display["Total Spend"] = df_display["Total Spend"].apply(lambda x: f"£{x:,.2f}" if isinstance(x, (int, float)) else x)
            df_display["Est. Delivery Date"] = df_display["Est. Delivery Date"].astype(str)
            df_display["Order No."] = df_display["Order No."].astype(str)

            html_table = df_display.to_html(index=False, escape=False, classes="custom-ledger-table")
            
            st.markdown(
                """
                <style>
                .custom-ledger-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: sans-serif;
                    margin: 10px 0;
                }
                .custom-ledger-table th {
                    background-color: #f0f2f6;
                    color: #31333F;
                    text-align: left;
                    padding: 12px;
                    border-bottom: 2px solid #e6e8f1;
                }
                .custom-ledger-table td {
                    padding: 12px;
                    border-bottom: 1px solid #e6e8f1;
                    vertical-align: top;
                    line-height: 1.5;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )
            
            st.markdown(html_table, unsafe_allow_html=True)