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
# 2. GARETH SOLOWAY LOGIC SCANNER FUNCTION
# ==========================================


def run_agent_scanner():
  """Scans a comprehensive US watchlist using Soloway-style technical criteria:

  - Long-term structural trend alignment (Price above 200-day MA).
  - Pullback proximity to major structural support (swing lows / key inflection).
  - Oversold momentum conditions (RSI dip) inside a macro bull trend.
  """
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
  print(
      f"Scanning {len(watchlist)} stocks using Gareth Soloway's support/trend"
      " logic..."
  )

  for ticker in watchlist:
    try:
      stock = yf.Ticker(ticker)
      # Pull 1 year of daily data to accurately find major swing levels and 200 DMA
      hist = stock.history(period="1yr")

      if hist.empty or len(hist) < 200:
        continue

      current_price = hist["Close"].iloc[-1]

      # Fundamentals context (Soloway values strong companies experiencing technical setups)
      info = stock.info
      pe_ratio = info.get("trailingPE")
      roe = info.get("returnOnEquity")
      roe_val = round(roe * 100, 2) if roe and roe != "N/A" else 0

      # --- Soloway Technical Logic Implementation ---
      # 1. Trend Structure: Must be structurally sound (Above 200-day moving average)
      ma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]
      is_macro_uptrend = current_price > ma_200

      # 2. Momentum / Pullback: 14-period RSI showing a dip (e.g., pulling back from highs)
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(rsi.iloc[-1], 2)
      is_pulling_back = current_rsi < 48

      # 3. Key Support Proximity: Check if price is sitting near its recent 3-month structural low
      # (Soloway focuses heavily on buying major tested support levels rather than chasing breakouts)
      three_month_low = hist["Low"].iloc[-60:].min()
      distance_to_support_pct = (
          (current_price - three_month_low) / three_month_low
      ) * 100
      # If current price is within 5% of its multi-month support base, it's at an inflection level
      is_near_support = distance_to_support_pct <= 5.0

      # Final Decision Rule combining trend, dip, and structural support proximity
      if is_macro_uptrend and is_pulling_back and is_near_support:
        stock_data = {
            "ticker": ticker,
            "price": round(current_price, 2),
            "support_level": round(three_month_low, 2),
            "pe": round(pe_ratio, 2) if pe_ratio else "N/A",
            "roe": roe_val,
            "rsi": current_rsi,
        }
        screaming_buys.append(stock_data)

    except Exception:
      continue

  save_history(screaming_buys)
  print(
      f"Scan complete. Found {len(screaming_buys)} setups matching key support"
      " criteria."
  )
  return screaming_buys


# ==========================================
# 3. EXECUTION GUARD
# ==========================================
if __name__ == "__main__":
  run_agent_scanner()
