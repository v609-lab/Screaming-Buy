from datetime import datetime
import json
import os
import streamlit as st

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

st.sidebar.markdown("---")
st.sidebar.header("📅 Historical Archive")

if not os.path.exists("history"):
  st.error("❌ The 'history' folder does not exist in your repository!")
else:
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

  if not available_dates:
    st.error("❌ No `.json` files found inside the `history` folder.")
  else:
    selected_date = st.sidebar.selectbox("Select Date to View:", available_dates)
    file_path = os.path.join("history", f"{selected_date}.json")

    st.subheader(f"📋 Market Rankings for: {selected_date}")

    if os.path.exists(file_path):
      try:
        with open(file_path, "r") as f:
          raw_data = f.read()

        # Debug text to verify file content on screen
        st.text(f"Raw file size: {len(raw_data)} bytes")

        data = json.loads(raw_data)
        stocks = data.get("stocks", [])

        st.info(f"Found {len(stocks)} stocks in the data payload.")

        if not stocks:
          st.warning(
              "The JSON file loaded, but the 'stocks' list is empty or missing."
          )
        else:
          for stock in stocks:
            rating = stock.get("rating", 5.0)
            ticker = stock.get("ticker", "UNKNOWN")
            price = stock.get("price", 0.0)

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
        st.error(f"❌ Error parsing JSON: {ex}")
    else:
      st.error(f"❌ File not found at path: {file_path}")
