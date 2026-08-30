from datetime import datetime
import json
import os
import pandas as pd
import yfinance as yf

# ==========================================
# 1. HISTORY SAVING FUNCTION
# ==========================================


def save_history(all_scored_stocks):
  """Saves daily results and ratings to a history folder for the web dashboard."""
  os.makedirs("history", exist_ok=True)
  today_str = datetime.now().strftime("%Y-%m-%d")
  filename = f"history/{today_str}.json"

  data = {
      "date": today_str,
      "total_scanned": len(all_scored_stocks),
      "stocks": all_scored_stocks,
  }

  with open(filename, "w") as f:
    json.dump(data, f, indent=4)
  print(f"Saved historical ratings to {filename}")


# ==========================================
# 2. ROBUST MARKET-CLOSED SCANNER
# ==========================================


def run_agent_scanner():
  """Scans the US watchlist using the latest available close price,

  evaluates technical levels, and outputs a 1-to-10 rating for every stock.
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

  all_scored_stocks = []
  print(f"Scanning {len(watchlist)} stocks using latest close prices...")

  for ticker in watchlist:
    try:
      stock = yf.Ticker(ticker)
      # Fetch 1 year of daily historical data
      hist = stock.history(period="1yr")

      if hist.empty or len(hist) < 200:
        continue

      # Use the absolute last available trading close price (handles weekends/holidays)
      current_price = float(hist["Close"].iloc[-1])

      # Fundamentals context with safe fallbacks
      info = stock.info
      pe_ratio = info.get("trailingPE")
      roe = info.get("returnOnEquity")
      roe_val = round(roe * 100, 2) if roe and roe != "N/A" else 15.0

      # --- Technical Calculations on Latest Data ---
      ma_200 = float(hist["Close"].rolling(window=200).mean().iloc[-1])
      is_macro_uptrend = current_price > ma_200

      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(float(rsi.iloc[-1]), 2)

      # 3-month structural low support level based on last 60 trading sessions
      three_month_low = float(hist["Low"].iloc[-60:].min())
      distance_to_support_pct = (
          (current_price - three_month_low) / three_month_low
      ) * 100

      # --- Scoring Engine (1 to 10 Scale) ---
      score = 5.0

      if is_macro_uptrend:
        score += 2.0
      else:
        score -= 2.0

      if distance_to_support_pct <= 3.0:
        score += 2.0
      elif distance_to_support_pct <= 7.0:
        score += 1.0
      elif distance_to_support_pct > 20.0:
        score -= 1.0

      if current_rsi < 40:
        score += 1.5
      elif current_rsi < 50:
        score += 0.5
      elif current_rsi > 75:
        score -= 1.5

      if roe_val > 12 and pe_ratio and pe_ratio < 40:
        score += 1.0

      final_rating = round(max(1.0, min(10.0, score)), 1)

      stock_data = {
          "ticker": ticker,
          "price": round(current_price, 2),
          "support_level": round(three_month_low, 2),
          "rating": final_rating,
          "pe": round(pe_ratio, 2) if pe_ratio else "N/A",
          "roe": roe_val,
          "rsi": current_rsi,
      }
      all_scored_stocks.append(stock_data)

    except Exception as e:
      print(f"Skipped {ticker}: {e}")
      continue

  # Sort by highest rating descending
  all_scored_stocks = sorted(
      all_scored_stocks, key=lambda x: x["rating"], reverse=True
  )

  save_history(all_scored_stocks)
  print(
      f"Scan complete. Successfully ranked {len(all_scored_stocks)} stocks using"
      " last close."
  )
  return all_scored_stocks


if __name__ == "__main__":
  run_agent_scanner()
