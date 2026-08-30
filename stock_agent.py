from datetime import datetime
import json
import os
import pandas as pd
import yfinance as yf

# ==========================================
# 1. HISTORY SAVING FUNCTION
# ==========================================


def save_history(screaming_buys):
  """Saves daily results to a history folder for the web dashboard."""
  os.makedirs("history", exist_ok=True)
  today_str = datetime.now().strftime("%Y-%m-%d")
  filename = f"history/{today_str}.json"

  data = {
      "date": today_str,
      "total_found": len(screaming_buys),
      "stocks": screaming_buys,
  }

  with open(filename, "w") as f:
    json.dump(data, f, indent=4)
  print(f"Saved historical results to {filename}")


# ==========================================
# 2. CORE AGENT SCANNER FUNCTION
# ==========================================


def run_agent_scanner():
  """Scans the stock watchlist using fundamental and technical criteria,

  saves history, and returns the list of screaming buys.
  """
  # Define your watchlist (you can add more tickers here)
  watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

  screaming_buys = []

  print(f"Starting scan for {len(watchlist)} stocks...")

  for ticker in watchlist:
    try:
      stock = yf.Ticker(ticker)
      hist = stock.history(period="6mo")

      if hist.empty or len(hist) < 50:
        continue

      current_price = hist["Close"].iloc[-1]

      # Basic metrics fetch (safely handled if missing data)
      info = stock.info
      pe_ratio = info.get("trailingPE", "N/A")
      roe = info.get("returnOnEquity", "N/A")
      if roe and roe != "N/A":
        roe = round(roe * 100, 2)

      # Simplified Technical Indicators calculation (RSI example)
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(rsi.iloc[-1], 2)

      # Example criteria logic (Adjust your thresholds as needed)
      # For demonstration, we collect stocks meeting basic criteria or all of them
      stock_data = {
          "ticker": ticker,
          "price": round(current_price, 2),
          "pe": pe_ratio,
          "roe": roe,
          "rsi": current_rsi,
      }

      # You can add your strict "Screaming Buy" filtering rules here:
      # if current_rsi < 40:
      screaming_buys.append(stock_data)

    except Exception as e:
      print(f"Error processing {ticker}: {e}")

  # Automatically save history whenever the scanner runs
  save_history(screaming_buys)

  return screaming_buys


# ==========================================
# 3. EXECUTION GUARD
# ==========================================
if __name__ == "__main__":
  # This block only triggers when run via GitHub Actions or terminal command.
  # It will NOT auto-execute when imported by your Streamlit web dashboard.
  run_agent_scanner()
