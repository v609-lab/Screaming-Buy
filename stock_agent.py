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
  """Scans a comprehensive US watchlist, saves history,

  and returns screaming buys.
  """
  # Comprehensive large-cap US stock watchlist
  watchlist = [
      "AAPL",
      "MSFT",
      "GOOGL",
      "AMZN",
      "NVDA",
      "META",
      "TSLA",
      "BRK-B",
      "JPM",
      "V",
      "JNJ",
      "WMT",
      "MA",
      "PG",
      "UNH",
      "HD",
      "DIS",
      "PYPL",
      "BAC",
      "XOM",
      "CVX",
      "PFE",
      "ABBV",
      "AVGO",
      "COST",
      "TMO",
      "CSCO",
      "ACN",
      "ABT",
      "DHR",
  ]

  screaming_buys = []
  print(f"Starting scan across {len(watchlist)} major US stocks...")

  for ticker in watchlist:
    try:
      stock = yf.Ticker(ticker)
      hist = stock.history(period="6mo")

      if hist.empty or len(hist) < 50:
        continue

      current_price = hist["Close"].iloc[-1]

      # Basic metrics fetch
      info = stock.info
      pe_ratio = info.get("trailingPE", "N/A")
      roe = info.get("returnOnEquity", "N/A")
      if roe and roe != "N/A":
        roe = round(roe * 100, 2)

      # Technical Indicators calculation (RSI)
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(rsi.iloc[-1], 2)

      stock_data = {
          "ticker": ticker,
          "price": round(current_price, 2),
          "pe": pe_ratio,
          "roe": roe,
          "rsi": current_rsi,
      }
      screaming_buys.append(stock_data)

    except Exception:
      continue

  save_history(screaming_buys)
  print(f"Scan complete. Found {len(screaming_buys)} total results.")
  return screaming_buys


# ==========================================
# 3. EXECUTION GUARD
# ==========================================
if __name__ == "__main__":
  run_agent_scanner()
