from datetime import datetime
import json
import os
import pandas as pd
import requests
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
# 2. BROWSER-DISGUISED TECHNICAL SCANNER
# ==========================================

def run_agent_scanner():
  """Scans the US watchlist using yfinance with a custom User-Agent
  to bypass Yahoo's cloud server blocking.
  """
  # Create a custom session disguised as a standard Chrome web browser
  session = requests.Session()
  session.headers.update({
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
  })

  watchlist = [
      "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
      "BRK-B", "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH",
      "HD", "DIS", "PYPL", "BAC", "XOM", "CVX", "PFE", "ABBV",
      "AVGO", "COST", "TMO", "CSCO", "ACN", "ABT", "DHR"
  ]

  all_scored_stocks = []
  print(f"Starting browser-disguised scan for {len(watchlist)} stocks...")

  for ticker in watchlist:
    try:
      # Pass the disguised session into yfinance
      stock = yf.Ticker(ticker, session=session)
      hist = stock.history(period="1yr")

      # If Yahoo still returns empty data, deliberately record the error to display it
      if hist.empty or len(hist) < 200:
        all_scored_stocks.append({
            "ticker": f"ERR: {ticker} Empty Data",
            "price": 0.0, "support_level": 0.0, "rating": 1.0, 
            "pe": "N/A", "roe": "N/A", "rsi": 0.0
        })
        continue

      current_price = float(hist["Close"].iloc[-1])

      # --- Soloway Technical Calculations ---
      ma_200 = float(hist["Close"].rolling(window=200).mean().iloc[-1])
      is_macro_uptrend = current_price > ma_200

      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(float(rsi.iloc[-1]), 2)

      three_month_low = float(hist["Low"].iloc[-60:].min())
      distance_to_support_pct = ((current_price - three_month_low) / three_month_low) * 100

      # --- Scoring Engine (1 to 10 Scale) ---
      score = 5.0

      if is_macro_uptrend: score += 2.5
      else: score -= 2.5

      if distance_to_support_pct <= 3.0: score += 2.0
      elif distance_to_support_pct <= 7.0: score += 1.0
      elif distance_to_support_pct > 25.0: score -= 1.0

      if current_rsi < 40: score += 1.5
      elif current_rsi < 50: score += 0.5
      elif current_rsi > 75: score -= 1.5

      final_rating = round(max(1.0, min(10.0, score)), 1)

      stock_data = {
          "ticker": ticker,
          "price": round(current_price, 2),
          "support_level": round(three_month_low, 2),
          "rating": final_rating,
          "pe": "N/A",  
          "roe": "N/A", 
          "rsi": current_rsi,
      }
      all_scored_stocks.append(stock_data)

    except Exception as e:
      all_scored_stocks.append({
          "ticker": f"ERR: {ticker} Exception",
          "price": 0.0, "support_level": 0.0, "rating": 1.0, 
          "pe": "N/A", "roe": "N/A", "rsi": 0.0
      })
      continue

  # Sort by highest rating descending
  all_scored_stocks = sorted(all_scored_stocks, key=lambda x: x["rating"], reverse=True)

  save_history(all_scored_stocks)
  return all_scored_stocks

if __name__ == "__main__":
  run_agent_scanner()
