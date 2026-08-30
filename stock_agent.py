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
  """Dynamically fetches the S&P 500 watchlist, scans them for fundamental

  and technical criteria, saves history, and returns screaming buys.
  """
  print("Fetching S&P 500 watchlist from Wikipedia...")
  try:
    table = pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    )
    watchlist = table[0]["Symbol"].tolist()
    # Clean up ticker symbols (Yahoo Finance uses '-' instead of '.' like BRK.B -> BRK-B)
    watchlist = [t.replace(".", "-") for t in watchlist]
  except Exception as e:
    print(f"Failed to fetch S&P 500 list, using fallback watchlist: {e}")
    watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

  screaming_buys = []
  print(
      f"Starting scan across {len(watchlist)} stocks (this may take a couple of"
      " minutes)..."
  )

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

      # Optional: You can filter here for strict "Screaming Buy" rules (e.g., RSI < 40)
      # For now, it compiles everything scanned successfully
      screaming_buys.append(stock_data)

    except Exception as e:
      # Silently skip individual errors to keep the bulk scan running smoothly
      continue

  # Automatically save history whenever the scanner runs
  save_history(screaming_buys)
  print(f"Scan complete. Found {len(screaming_buys)} total results.")

  return screaming_buys


# ==========================================
# 3. EXECUTION GUARD
# ==========================================
if __name__ == "__main__":
  run_agent_scanner()
