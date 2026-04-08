import streamlit as st
import requests
import time

# Page configuration
st.set_page_config(page_title="AI Logistics Router", layout="wide")
st.title("🚀 Live AI Logistics Router Dashboard")
st.write("Watch the AI agent optimize the supply chain in real-time.")

# API Endpoint (Jahan tumhara Docker chal raha hai)
API_URL = "http://127.0.0.1:7860/state"

# Auto-refresh loop ke liye ek placeholder
placeholder = st.empty()

# Tum chaho toh manual refresh button bhi use kar sakti ho
st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (Live Tracking)", value=False)

try:
    with placeholder.container():
        # Backend se data fetch karna
        response = requests.get(API_URL)
        
        if response.status_code == 200:
            data = response.json()
            obs = data.get("observation", {})
            
            # --- TOP ROW: KPI Metrics ---
            col1, col2, col3 = st.columns(3)
            
            budget = obs.get('budget_remaining', 0)
            pending_orders = len([o for o in obs.get('orders', []) if o.get('status') == 'PENDING'])
            reward = data.get('reward', 0)
            
            col1.metric("💰 Budget Remaining", f"${budget}")
            col2.metric("📦 Pending Orders", pending_orders)
            col3.metric("🏆 Last Reward", f"{reward:.2f}")
            
            st.markdown("---")
            
            # --- MIDDLE ROW: Warehouses ---
            st.subheader("🏢 Warehouse Live Inventory")
            w_col1, w_col2, w_col3 = st.columns(3)
            
            inventory = obs.get("inventory", {})
            la_stock = inventory.get("Warehouse_LA", {}).get("Laptop", 0)
            chi_stock = inventory.get("Warehouse_CHI", {}).get("Laptop", 0)
            ny_stock = inventory.get("Warehouse_NY", {}).get("Laptop", 0)
            
            with w_col1:
                st.info(f"**📍 Warehouse LA**\n\n📦 {la_stock} Units\n\n⏳ Transit: 6 Days")
            with w_col2:
                st.warning(f"**📍 Warehouse CHI**\n\n📦 {chi_stock} Units\n\n⏳ Transit: 2 Days")
            with w_col3:
                st.success(f"**🎯 Target (NY)**\n\n📦 {ny_stock} Units Delivered")
                
            st.markdown("---")
            st.caption(f"System Status: {obs.get('last_action_feedback', 'Online')}")

        else:
            st.error("Waiting for backend API to start...")
            
except Exception as e:
    st.error("Server is down. Ensure your Docker container is running on port 7860.")

# Auto-refresh logic (har 1 second mein screen update hogi)
if auto_refresh:
    time.sleep(1)
    st.rerun()