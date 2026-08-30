from datetime import datetime
import json
import os
import streamlit as st

# Optional: Safely try importing your scanner if available
try:
  from stock_agent import run_agent_scanner
except ImportError:
  run_agent_scanner = None

st.set_page_config(
    page_title="Stock Market Rating Dashboard", page_icon="📊", layout="wide"
)

st.title("📊 Institutional Stock Rating & Analysis Dashboard")
st.markdown(
    "Automated 1-to-10 Scoring (1 = Avoid, 10 = Strong Buy) using Gareth"
    " Soloway Technical Support Levels & Moat Metrics."
)

st.sidebar.header("⚙️ Agent Controls")
if run_agent_scanner:
  if st.sidebar.button("🚀 Run Live Market Scan Now"):
    with st.spinner("Analyzing charts, support levels, and valuations..."):
      try:
        run_agent_scanner()
        st.sidebar.success("Scan completed successfully!")
        st.rerun()
      except Exception as e:
        st.sidebar.error(f"Error running scan: {e}")
else:
  st.sidebar.info("Agent scanner function not imported.")

st.sidebar.markdown("---")
st.sidebar.header("📅 Historical Archive")

if not os.path.exists("history"):
  st.warning("The 'history' directory does not exist yet.")
else:
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

  if not available_dates:
    st.warning("No history JSON files found in the history folder.")
  else:
    selected_date = st.sidebar.selectbox("Select Date to View:", available_dates)
    file_path = os.path.join("history", f"{selected_date}.json")

    if os.path.exists(file_path):
      try:
        with open(file_path, "r") as f:
          data = json.load(f)

        st.subheader(f"📋 Market Rankings for: {data.get('date', selected_date)}")
        stocks = data.get("stocks", [])

        if not stocks:
          st.info("The history file is empty or contains no stocks list.")
        else:
          st.write(f"Successfully loaded {len(stocks)} ranked stocks:")

          for stock in stocks:
            rating = stock.get("rating", 5.0)
            ticker = stock.get("ticker", "UNKNOWN")
            price = stock.get("price", 0.0)

            # Dynamic color badges
            if rating >= 8.0:
              badge = "🟢 **STRONG BUY**"
            elif rating >= 6.0:
              badge = "🟡 **HOLD / WATCH**"
            else:
              badge = "🔴 **AVOID / WEAK**"

            with st.expander(
                f"{badge} | {ticker} — Rating: {rating}/10 — Price: ${price}"
            ):
              c1, c2, c3, c4, c5 = st.columns(5)
              c1.metric("Rating Score", f"{rating} / 10")
              c2.metric("Current Price", f"${price}")
              c3.metric(
                  "Key Support Level", f"${stock.get('support_level', 'N/A')}"
              )
              c4.metric("RSI (14)", stock.get("rsi", "N/A"))
              c5.metric("P/E Ratio", stock.get("pe", "N/A"))

      except Exception as ex:
        st.error(f"Error reading JSON file: {ex}")
    else:
      st.error(f"Data file not found at {file_path}")
