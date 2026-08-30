import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import yfinance as yf

# ==========================================
# CONFIGURATION & SETTINGSss
# ==========================================
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# Fetch credentials securely from environment variables (GitHub Secrets)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")


# ==========================================
# AGENT 1: FUNDAMENTAL & MOAT ANALYZER
# ==========================================
def analyze_fundamentals(ticker_symbol):
  try:
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    pe_ratio = info.get("trailingPE", 999)
    forward_pe = info.get("forwardPE", 999)
    roe = info.get("returnOnEquity", 0)
    profit_margins = info.get("profitMargins", 0)
    revenue_growth = info.get("revenueGrowth", 0)

    moat_score = 0
    if roe and roe > 0.15:
      moat_score += 1
    if profit_margins and profit_margins > 0.10:
      moat_score += 1
    if revenue_growth and revenue_growth > 0.08:
      moat_score += 1

    fundamentals_passed = (
        pe_ratio < 45 and forward_pe < 40 and moat_score >= 2
    )

    return {
        "passed": fundamentals_passed,
        "pe": pe_ratio,
        "roe": round(roe * 100, 2) if roe else 0,
        "growth": round(revenue_growth * 100, 2) if revenue_growth else 0,
    }
  except Exception as e:
    print(f"Error fetching fundamentals for {ticker_symbol}: {e}")
    return {"passed": False}


# ==========================================
# AGENT 2: TECHNICAL ANALYST
# ==========================================
def analyze_technicals(ticker_symbol):
  try:
    df = yf.download(
        ticker_symbol, period="1y", interval="1d", progress=False
    )
    if df.empty or len(df) < 200:
      return {"passed": False}

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    close_prices = df["Close"]
    high_prices = df["High"]
    low_prices = df["Low"]
    current_price = float(close_prices.iloc[-1])

    # Moving Averages
    sma_50 = float(close_prices.rolling(window=50).mean().iloc[-1])
    sma_200 = float(close_prices.rolling(window=200).mean().iloc[-1])
    long_term_bullish = (current_price > sma_50) and (sma_50 > sma_200)

    # RSI (14)
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])
    rsi_healthy = 40 <= current_rsi <= 65

    # MACD (12, 26, 9)
    exp1 = close_prices.ewm(span=12, adjust=False).mean()
    exp2 = close_prices.ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    current_macd = float(macd_line.iloc[-1])
    current_signal = float(signal_line.iloc[-1])
    prev_macd = float(macd_line.iloc[-2])
    prev_signal = float(signal_line.iloc[-2])
    macd_crossover = (prev_macd <= prev_signal) and (
        current_macd > current_signal
    )

    # Fibonacci Retracement (6-Month Lookback)
    recent_df = df.tail(126)
    max_high = float(recent_df["High"].max())
    min_low = float(recent_df["Low"].min())
    diff = max_high - min_low
    fib_382 = max_high - (diff * 0.382)
    fib_618 = max_high - (diff * 0.618)
    near_fib_support = fib_618 <= current_price <= fib_382

    technical_passed = (
        long_term_bullish and rsi_healthy and macd_crossover and near_fib_support
    )

    return {
        "passed": technical_passed,
        "price": round(current_price, 2),
        "rsi": round(current_rsi, 2),
    }
  except Exception as e:
    print(f"Error computing technicals for {ticker_symbol}: {e}")
    return {"passed": False}


# ==========================================
# AGENT 3: EMAIL NOTIFICATION
# ==========================================
def send_email_alert(screaming_buys):
  if not screaming_buys:
    print("No screaming buys found today. Skipping email.")
    return

  html_content = """
    <h2>🚨 Stock Agent Alert: Screaming Buy Opportunities Found! 🚨</h2>
    <p>The following US stocks match strict fundamental and technical criteria:</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; text-align: left;">
        <tr style="background-color: #f2f2f2;">
            <th>Ticker</th>
            <th>Price ($)</th>
            <th>P/E Ratio</th>
            <th>ROE (%)</th>
            <th>RSI (14)</th>
        </tr>
    """

  for item in screaming_buys:
    html_content += f"""
        <tr>
            <td><b>{item['ticker']}</b></td>
            <td>{item['price']}</td>
            <td>{item['pe']}</td>
            <td>{item['roe']}%</td>
            <td>{item['rsi']}</td>
        </tr>
        """

  html_content += """
    </table>
    <p><br><i>Generated automatically by your GitHub Actions Agent.</i></p>
    """

  msg = MIMEMultipart()
  msg["From"] = SENDER_EMAIL
  msg["To"] = RECEIVER_EMAIL
  msg["Subject"] = (
      f"🚨 Screaming Buy Alert: {len(screaming_buys)} Stock(s) Found!"
  )
  msg.attach(MIMEText(html_content, "html"))

  try:
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print("Email alert successfully sent!")
  except Exception as e:
    print(f"Failed to send email: {e}")


# ==========================================
# MAIN ORCHESTRATION
# ==========================================
def run_agent_scanner():
  print("Running US Stock Screaming Buy Agent Scanner...")
  screaming_buys = []

  for ticker in WATCHLIST:
    print(f"Analyzing {ticker}...")
    fund_res = analyze_fundamentals(ticker)
    tech_res = analyze_technicals(ticker)

    if fund_res.get("passed") and tech_res.get("passed"):
      print(f"🔥 SCREAMING BUY FOUND: {ticker}")
      screaming_buys.append({
          "ticker": ticker,
          "price": tech_res["price"],
          "pe": fund_res["pe"],
          "roe": fund_res["roe"],
          "rsi": tech_res["rsi"],
      })

  send_email_alert(screaming_buys)


if __name__ == "__main__":
  run_agent_scanner()
