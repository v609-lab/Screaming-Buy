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

# -----------------------------------------
# SIDEBAR CONTROLLER
# -----------------------------------------
st.sidebar.header("⚙️ Agent Controls")

if run_agent_scanner:
  if st.sidebar.button("🚀 Run Live Market Scan Now"):
    with st.spinner(
        "Scanning the market, analyzing charts and support levels... Please"
        " wait (~30 secs)..."
    ):
      try:
        # 1. Execute live scan and save today's json file
        run_agent_scanner()
        st.sidebar.success("Live market scan completed successfully!")
        # Save state to automatically select today's date after reload
        st.session_state["auto_select_today"] = True
        st.rerun()
      except Exception as e:
        st.sidebar.error(f"Error running scan: {e}")
else:
  st.sidebar.error("Could not import stock_agent.py scanner function.")

st.sidebar.markdown("---")
st.sidebar.header("📅 Historical Archive")

# -----------------------------------------
# RENDER HISTORICAL OR LIVE DATA
# -----------------------------------------
if not os.path.exists("history"):
  st.warning(
      "No history folder found yet. Click 'Run Live Market Scan Now' on the"
      " sidebar to generate your first live list!"
  )
else:
  files = sorted(os.listdir("history"), reverse=True)
  available_dates = [f.replace(".json", "") for f in files if f.endswith(".json")]

  if not available_dates:
    st.warning("No data files found in history folder.")
  else:
    # Default selection logic
    default_index = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    if st.session_state.get("auto_select_today", False) and today_str in available_dates:
      default_index = available_dates.index(today_str)
      st.session_state["auto_select_today"] = False

    selected_date = st.sidebar.selectbox(
        "Select Date to View:", available_dates, index=default_index
    )
    file_path = os.path.join("history", f"{selected_date}.json")

    st.subheader(f"📋 Market Rankings for: {selected_date}")

    if os.path.exists(file_path):
      try:
        with open(file_path, "r") as f:
          data = json.load(f)

        stocks = data.get("stocks", [])

        if not stocks:
          st.info(
              "The scan ran, but no stocks were returned in the payload."
          )
        else:
          st.success(
              f"Successfully loaded {len(stocks)} evaluated stocks from the"
              " market scan!"
          )

          for stock in stocks:
            rating = stock.get("rating", 5.0)
            ticker = stock.get("ticker", "UNKNOWN")
            price = stock.get("price", 0.0)

            # Color-coded ranking badges
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
      st.error(f"Data file not found at path: {file_path}")
