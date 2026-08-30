from datetime import datetime, timedelta
import json
import os
import streamlit as st

st.set_page_config(
    page_title="Screaming Buy Stock Agent", page_icon="🚀", layout="wide"
)

st.title("🚀 US Stock 'Screaming Buy' Dashboard")
st.markdown(
    "Automated Fundamental Moat + Technical Analysis (MACD, RSI, Fibonacci,"
    " SMAs)"
)

# Sidebar: Date selection for the last 15 days
st.sidebar.header("📅 Historical Archive")
available_dates = []
if os.path.exists("history"):
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

if not available_dates:
  st.warning(
      "No historical data found yet. Run your GitHub Action to generate"
      " results!"
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

      # Format into a clean table display
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

# Refresh button
if st.button("🔄 Refresh Data"):
  st.rerun()
