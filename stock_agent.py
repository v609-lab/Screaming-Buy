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
# 2. SOLOWAY-STYLE SCORING AGENT
# ==========================================


def run_agent_scanner():
  """Scans the US watchlist, calculates Soloway technical levels,

  applies fundamental weights, and outputs a 1-to-10 rating for every stock.
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
  print(
      f"Scoring {len(watchlist)} stocks using institutional rating logic..."
  )

  for ticker in watchlist:
    try:
      stock = yf.Ticker(ticker)
      hist = stock.history(period="1yr")

      if hist.empty or len(hist) < 200:
        continue

      current_price = hist["Close"].iloc[-1]

      # Fundamentals context
      info = stock.info
      pe_ratio = info.get("trailingPE")
      roe = info.get("returnOnEquity")
      roe_val = round(roe * 100, 2) if roe and roe != "N/A" else 10.0

      # --- Soloway Technical Calculations ---
      # 1. Trend Structure (200-day Moving Average)
      ma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]
      is_macro_uptrend = current_price > ma_200

      # 2. RSI Momentum
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi = 100 - (100 / (1 + rs))
      current_rsi = round(rsi.iloc[-1], 2)

      # 3. Support Proximity (Distance to 3-month structural low)
      three_month_low = hist["Low"].iloc[-60:].min()
      distance_to_support_pct = (
          (current_price - three_month_low) / three_month_low
      ) * 100

      # --- Scoring Engine (1 to 10 Scale) ---
      # Base score starts at 5 (Neutral)
      score = 5.0

      # Factor A: Macro Trend (Soloway rule: never fight the 200 DMA structural trend)
      if is_macro_uptrend:
        score += 2.0
      else:
        score -= 2.0

      # Factor B: Support Proximity (Bonus points if sitting right at key multi-month support)
      if distance_to_support_pct <= 3.0:
        score += 2.0  # Tagging major structural support zone
      elif distance_to_support_pct <= 7.0:
        score += 1.0
      elif distance_to_support_pct > 20.0:
        score -= 1.0  # Extended far away from support (chasing highs)

      # Factor C: RSI Momentum Exhaustion (Reward pullbacks inside a bull trend)
      if current_rsi < 40:
        score += 1.5  # Oversold dip / high probability bounce zone
      elif current_rsi < 50:
        score += 0.5
      elif current_rsi > 75:
        score -= 1.5  # Overbought / vulnerable to reversal

      # Factor D: Business Moat & Valuation Check
      if roe_val > 15 and pe_ratio and pe_ratio < 35:
        score += 1.0  # Quality compounder at a fair price
      elif pe_ratio and pe_ratio > 50:
        score -= 1.0  # Overvalued risk

      # Clamp final score strictly between 1 and 10, rounded to 1 decimal place
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

    except Exception:
      continue

  # Sort stocks from highest rating to lowest rating
  all_scored_stocks = sorted(
      all_scored_stocks, key=lambda x: x["rating"], reverse=True
  )

  save_history(all_scored_stocks)
  print(
      f"Scan complete. Scored and ranked {len(all_scored_stocks)} total"
      " stocks."
  )
  return all_scored_stocks


# ==========================================
# 3. EXECUTION GUARD
# ==========================================
if __name__ == "__main__":
  run_agent_scanner()
