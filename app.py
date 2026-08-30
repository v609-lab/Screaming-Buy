from datetime import datetime
import json
import os
import streamlit as st

# Import your agent function directly
from stock_agent import run_agent_scanner  # Make sure this matches your function name

st.set_page_config(
    page_title="Screaming Buy Stock Agent", page_icon="🚀", layout="wide"
)

st.title("🚀 US Stock 'Screaming Buy' Dashboard")
st.markdown(
    "Automated Fundamental Moat + Technical Analysis (MACD, RSI, Fibonacci,"
    " SMAs)"
)

# -----------------------------------------
# SIDEBAR: ON-DEMAND RUNNER & ARCHIVE
# -----------------------------------------
st.sidebar.header("⚙️ Agent Controls")

if st.sidebar.button("🚀 Run Stock Agent Now"):
  with st.spinner(
      "Running fundamental and technical analysis... Please wait (~15-30"
      " seconds)..."
  ):
    try:
      # Run the function directly in memory using Streamlit's Python environment
      run_agent_scanner()
      st.sidebar.success("Agent scan completed successfully!")
      st.rerun()  # Refresh the page to load new results
    except Exception as e:
      st.sidebar.error(f"Failed to execute agent: {e}")

st.sidebar.markdown("---")
st.sidebar.header("📅 Historical Archive")

# Load available history dates
available_dates = []
if os.path.exists("history"):
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

if not available_dates:
  st.warning(
      "No historical data found yet. Click the 'Run Stock Agent Now' button on"
      " the sidebar to generate your first list!"
  )
else:
  # Default to the most recent date
  selected_date = st.sidebar.selectbox("Select Date to View:", available_dates)

  # Load data for selected date
  file_path = os.path.join("history", f"{selected_date}.json")
  if os.path.exists(file_path):
    with open(file_path, "r") as f:
      data = json.load(f)

    st.subheader(f"📊 Results for: {data.get('date')}")

    stocks = data.get("stocks", [])
    if not stocks:
      st.info(
          "No 'Screaming Buy' stocks matched the strict criteria on this date."
      )
    else:
      st.success(
          f"Found {len(stocks)} Screaming Buy opportunity(ies) on this date!"
      )

      # Display stocks in a clean card layout
      for stock in stocks:
        with st.expander(
            f"🔥 {stock['ticker']} — Price: ${stock['price']}"
        ):
          col1, col2, col3, col4 = st.columns(4)
          col1.metric("Current Price", f"${stock['price']}")
          col2.metric("P/E Ratio", stock["pe"])
          col3.metric("ROE", f"{stock['roe']}%")
          col4.metric("RSI (14)", stock["rsi"])
  else:
    st.error("Data file not found.")
