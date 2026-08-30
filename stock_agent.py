from datetime import datetime
import json
import os
import requests
import pandas as pd

# Hardcoded FMP API Key for guaranteed connection
FMP_API_KEY = "GOfOMQRJ96YOqTdNJ5NEIqw6cAdw2aRO"

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
# 2. FMP API TECHNICAL SCANNER
# ==========================================

def run_agent_scanner():
  """Scans the US watchlist using official Financial Modeling Prep data."""
  
  watchlist = [
      "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
      "BRK-B", "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH",
      "HD", "DIS", "PYPL", "BAC", "XOM", "CVX", "PFE", "ABBV",
      "AVGO", "COST", "TMO", "CSCO", "ACN", "ABT", "DHR"
  ]

  all_scored_stocks = []
  print(f"Starting API scan for {len(watchlist)} stocks...")

  for ticker in watchlist:
    try:
      # Fetch 250 trading days of history to cover the 200-day moving average
      url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?timeseries=250&apikey={FMP_API_KEY}"
      response = requests.get(url)
      
      if response.status_code != 200:
        print(f"Failed to fetch {ticker}: {response.status_code}")
        continue
        
      data = response.json()
      historical = data.get("historical", [])
      
      if len(historical) < 200:
        print(f"Not enough historical data for {ticker}")
        continue

      # Convert API JSON to DataFrame and reverse order to chronological (oldest to newest)
      df = pd.DataFrame(historical)
      df = df.iloc[::-1].reset_index(drop=True)

      current_price = float(df["close"].iloc[-1])

      # --- Soloway Technical Calculations ---
      # 1. Macro Trend Structure (200-day Moving Average)
      ma_200 = float(df["close"].rolling(window=200).mean().iloc[-1])
      is_macro_uptrend = current_price > ma_200

      # 2. RSI Momentum (14-period)
      delta = df["close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(float(rsi.iloc[-1]), 2)

      # 3. Support Proximity (Distance to 60-day low)
      three_month_low = float(df["low"].iloc[-60:].min())
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
          "pe": "N/A",  
          "roe": "N/A", 
          "rsi": current_rsi,
      }
      all_scored_stocks.append(stock_data)

    except Exception as e:
      print(f"Error processing {ticker}: {e}")
      continue

  # Sort by highest rating descending
  all_scored_stocks = sorted(all_scored_stocks, key=lambda x: x["rating"], reverse=True)

  save_history(all_scored_stocks)
  print(f"Scan complete. Ranked {len(all_scored_stocks)} stocks.")
  return all_scored_stocks

if __name__ == "__main__":
  run_agent_scanner()
