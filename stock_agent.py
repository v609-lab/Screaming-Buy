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
# 2. PURE PRICE-ACTION SCANNER
# ==========================================

def run_agent_scanner():
  """Scans the US watchlist using pure yfinance price history,
  bypassing the blocked fundamental .info endpoints.
  """
  watchlist = [
      "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
      "BRK-B", "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH",
      "HD", "DIS", "PYPL", "BAC", "XOM", "CVX", "PFE", "ABBV",
      "AVGO", "COST", "TMO", "CSCO", "ACN", "ABT", "DHR"
  ]

  all_scored_stocks = []
  print(f"Starting pure price-action scan for {len(watchlist)} stocks...")

  for ticker in watchlist:
    try:
      # Fetch 1 year of daily history (Does NOT get blocked like .info does)
      stock = yf.Ticker(ticker)
      hist = stock.history(period="1yr")

      if hist.empty or len(hist) < 200:
        continue

      current_price = float(hist["Close"].iloc[-1])

      # --- Soloway Technical Calculations ---
      # 1. Macro Trend Structure (200-day Moving Average)
      ma_200 = float(hist["Close"].rolling(window=200).mean().iloc[-1])
      is_macro_uptrend = current_price > ma_200

      # 2. RSI Momentum (14-period)
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(float(rsi.iloc[-1]), 2)

      # 3. Support Proximity (Distance to 60-day low)
      three_month_low = float(hist["Low"].iloc[-60:].min())
      distance_to_support_pct = ((current_price - three_month_low) / three_month_low) * 100

      # --- Scoring Engine (1 to 10 Scale) ---
      score = 5.0

      if is_macro_uptrend:
        score += 2.5
      else:
        score -= 2.5

      if distance_to_support_pct <= 3.0:
        score += 2.0
      elif distance_to_support_pct <= 7.0:
        score += 1.0
      elif distance_to_support_pct > 25.0:
        score -= 1.0

      if current_rsi < 40:
        score += 1.5
      elif current_rsi < 50:
        score += 0.5
      elif current_rsi > 75:
        score -= 1.5

      final_rating = round(max(1.0, min(10.0, score)), 1)

      stock_data = {
          "ticker": ticker,
          "price": round(current_price, 2),
          "support_level": round(three_month_low, 2),
          "rating": final_rating,
          "pe": "N/A",  # Hardcoded N/A to avoid getting blocked
          "roe": "N/A", # Hardcoded N/A to avoid getting blocked
          "rsi": current_rsi,
      }
      all_scored_stocks.append(stock_data)

    except Exception as e:
      print(f"Error processing {ticker}: {e}")
      continue

  # If network still drops everything, provide the mock fallback
  if not all_scored_stocks:
    all_scored_stocks = [{
        "ticker": "ERR: Network Blocked", "price": 0.0, "support_level": 0.0, 
        "rating": 1.0, "pe": "N/A", "roe": "N/A", "rsi": 0.0
    }]

  # Sort by highest rating descending
  all_scored_stocks = sorted(all_scored_stocks, key=lambda x: x["rating"], reverse=True)

  save_history(all_scored_stocks)
  return all_scored_stocks

if __name__ == "__main__":
  run_agent_scanner()
