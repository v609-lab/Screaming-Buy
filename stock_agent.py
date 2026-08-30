from datetime import datetime
import json
import os
import requests
import pandas as pd

FMP_API_KEY = "GOfOMQRJ96YOqTdNJ5NEIqw6cAdw2aRO"

# ==========================================
# 1. HISTORY SAVING FUNCTION
# ==========================================

def save_history(all_scored_stocks):
  os.makedirs("history", exist_ok=True)
  today_str = datetime.now().strftime("%Y-%m-%d")
  filename = f"history/{today_str}.json"
  with open(filename, "w") as f:
    json.dump({
        "date": today_str,
        "total_scanned": len(all_scored_stocks),
        "stocks": all_scored_stocks
    }, f, indent=4)

# ==========================================
# 2. DIAGNOSTIC SCANNER
# ==========================================

def run_agent_scanner():
  # Testing with a small list to get the error immediately
  watchlist = ["AAPL", "MSFT"]
  all_scored_stocks = []

  for ticker in watchlist:
    try:
      url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?timeseries=250&apikey={FMP_API_KEY}"
      response = requests.get(url, timeout=10)
      
      # If FMP rejects the request, deliberately trigger an error to read the message
      if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text[:60]}")
        
      data = response.json()
      
      if "historical" not in data:
        raise Exception(f"No historical data. API said: {str(data)[:60]}")

      historical = data["historical"]
      if len(historical) < 200:
        raise Exception(f"Only {len(historical)} days of data available.")

      df = pd.DataFrame(historical)
      df = df.iloc[::-1].reset_index(drop=True)
      current_price = float(df["close"].iloc[-1])

      all_scored_stocks.append({
          "ticker": ticker,
          "price": round(current_price, 2),
          "support_level": 0.0,
          "rating": 10.0,
          "pe": "N/A",  
          "roe": "N/A", 
          "rsi": 50.0,
      })

    except Exception as e:
      # INJECT THE ERROR MESSAGE DIRECTLY INTO THE DASHBOARD UI!
      all_scored_stocks.append({
          "ticker": f"ERR: {str(e)}",
          "price": 0.0,
          "support_level": 0.0,
          "rating": 1.0,
          "pe": "N/A",  
          "roe": "N/A", 
          "rsi": 0.0,
      })

  save_history(all_scored_stocks)
  return all_scored_stocks

if __name__ == "__main__":
  run_agent_scanner()
