from datetime import datetime
import json
import os
import streamlit as st
from stock_agent import run_agent_scanner

st.set_page_config(
    page_title="Stock Market Rating Dashboard", page_icon="📊", layout="wide"
)

st.title("📊 Institutional Stock Rating & Analysis Dashboard")
st.markdown(
    "Automated 1-to-10 Scoring (1 = Avoid, 10 = Strong Buy) using Gareth"
    " Soloway Technical Support Levels & Moat Metrics."
)

st.sidebar.header("⚙️ Agent Controls")
if st.sidebar.button("🚀 Run Live Market Scan Now"):
  with st.spinner("Analyzing charts, support levels, and valuations..."):
    try:
      run_agent_scanner()
      st.sidebar.success("Scan completed successfully!")
      st.rerun()
    except Exception as e:
      st.sidebar.error(f"Error running scan: {e}")

st.sidebar.markdown("---")
st.sidebar.header("📅 Historical Archive")

available_dates = []
if os.path.exists("history"):
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

if not available_dates:
  st.warning(
      "No history found. Click 'Run Live Market Scan Now' on the sidebar."
  )
else:
  selected_date = st.sidebar.selectbox("Select Date to View:", available_dates)
  file_path = os.path.join("history", f"{selected_date}.json")

  if os.path.exists(file_path):
    with open(file_path, "r") as f:
      data = json.load(f)

    st.subheader(f"📋 Market Rankings for: {data.get('date')}")
    stocks = data.get("stocks", [])

    for stock in stocks:
      rating = stock["rating"]

      # Dynamic color coding based on score
      if rating >= 8.0:
        badge = "🟢 **STRONG BUY**"
      elif rating >= 6.0:
        badge = "🟡 **HOLD / WATCH**"
      else:
        badge = "🔴 **AVOID / WEAK**"

      with st.expander(
          f"{badge} | {stock['ticker']} — Rating: {rating}/10 — Price:"
          f" ${stock['price']}"
      ):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Rating Score", f"{rating} / 10")
        c2.metric("Current Price", f"${stock['price']}")
        c3.metric("Key Support Level", f"${stock['support_level']}")
        c4.metric("RSI (14)", stock["rsi"])
        c5.metric("P/E Ratio", stock["pe"])
  else:
    st.error("Data file not found.")
