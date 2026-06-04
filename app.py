import streamlit as st
import pandas as pd
import plotly.express as px
# import google.generativeai as genai (Install via pip)

st.set_page_config(page_title="Smart Supply Platform", layout="wide")

# 1. Navigation / Role Selection
role = st.sidebar.selectbox("Select View", ["Customer Portal", "Operations & Analytics"])

# Mock Supplier Data for the PoC
MOCK_SUPPLIERS = {
    "Supplier A": {"cement": 10.50, "drywall": 15.00},
    "Supplier B": {"cement": 11.00, "drywall": 14.20}
}

if role == "Customer Portal":
    st.title("📦 Smart Order Portal")
    st.subheader("Tell us what you need")
    
    # Natural Language Input
    user_input = st.text_area(
        "Describe your order request naturally:", 
        placeholder="e.g., I need 10 bags of cement by next Friday..."
    )
    
    if st.button("Process with AI"):
        with st.spinner("AI parsing your request..."):
            # Here you would call Gemini API with a structured prompt to return JSON
            # Mocking the AI response for now:
            parsed_items = {"cement": 10} 
            target_date = "2026-06-12"
            
            st.success("AI parsed your request successfully!")
            
            # Fetch prices from "APIs"
            results = []
            for supplier, stock in MOCK_SUPPLIERS.items():
                if "cement" in stock:
                    cost = stock["cement"] * parsed_items["cement"]
                    results.append({"Supplier": supplier, "Item": "Cement", "Total Cost (£)": cost, "Delivery Date": target_date})
            
            df_results = pd.DataFrame(results)
            st.dataframe(df_results)
            
            if st.button("Confirm Best Deal"):
                # Here you would insert this data into Supabase to log it for analytics
                st.balloons()
                st.success("Order logged and sent to operations!")

elif role == "Operations & Analytics":
    st.title("📊 Market Intelligence & Ops Dashboard")
    
    # Mocking data pulled from your "Supabase Data Lake"
    analytics_data = pd.DataFrame([
        {"Date": "2026-06-01", "Item": "Cement", "Avg_Price": 10.50, "Volume": 150},
        {"Date": "2026-06-02", "Item": "Cement", "Avg_Price": 10.75, "Volume": 200},
        {"Date": "2026-06-03", "Item": "Cement", "Avg_Price": 10.60, "Volume": 350},
        {"Date": "2026-06-04", "Item": "Drywall", "Avg_Price": 14.50, "Volume": 90},
    ])
    
    st.subheader("Data Lake Transformation Layer (In-Memory)")
    item_filter = st.selectbox("Select Item to Analyze Data Trends", analytics_data["Item"].unique())
    
    # Quick transformation using Pandas
    filtered_df = analytics_data[analytics_data["Item"] == item_filter]
    
    # Visualization Layer
    fig = px.line(filtered_df, x="Date", y="Avg_Price", title=f"Market Price Trends: {item_filter}", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("This visualization demonstrates the data monetization layer for premium subscribers.")