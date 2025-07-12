
from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup
import json

from fastapi_utils.tasks import repeat_every
import datetime

from fastapi import APIRouter
router = APIRouter()

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


import yfinance as yf

def fetch_yahoo_historical(symbol):
    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period="6mo")
        return hist['Close'].tolist()
    except Exception as e:
        print(f"[ERROR] Yahoo Finance fetch failed for {symbol}: {e}")
        return []

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Technical indicator calculation (extended with MACD, Bollinger Bands, and real RSI)
def calculate_technical_analysis(data):
    try:
        symbol = data.get("symbol") or data.get("stock") or ""
        prices = fetch_yahoo_historical(symbol)
        if len(prices) < 50:
            return {"error": "Not enough historical data for analysis"}

        def ema(prices, span):
            ema_values = [prices[0]]
            k = 2 / (span + 1)
            for price in prices[1:]:
                ema_values.append((price * k) + (ema_values[-1] * (1 - k)))
            return ema_values

        sma_50 = sum(prices[-50:]) / 50
        sma_200 = sum(prices[-200:]) / 200 if len(prices) >= 200 else None

        # MACD (12 EMA - 26 EMA)
        ema_12 = ema(prices, 12)
        ema_26 = ema(prices, 26)
        macd_series = [a - b for a, b in zip(ema_12[-len(ema_26):], ema_26)]
        macd = macd_series[-1]

        # Bollinger Bands
        sma_20 = sum(prices[-20:]) / 20
        std_dev = (sum((p - sma_20) ** 2 for p in prices[-20:]) / 20) ** 0.5
        upper_band = sma_20 + 2 * std_dev
        lower_band = sma_20 - 2 * std_dev
        price = prices[-1]

        signal = []
        if sma_50 and sma_200:
            signal.append("Golden Cross (Bullish)" if sma_50 > sma_200 else "Death Cross (Bearish)")

        signal.append("MACD Bullish" if macd > 0 else "MACD Bearish")

        if price > upper_band:
            signal.append("Above Upper Band (Overbought)")
        elif price < lower_band:
            signal.append("Below Lower Band (Oversold)")
        else:
            signal.append("Within Bands (Normal)")

        # RSI (14-day)
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas[-14:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-14:]]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        if rsi < 30:
            signal.append("RSI Oversold")
        elif rsi > 70:
            signal.append("RSI Overbought")
        else:
            signal.append("RSI Neutral")

        # Trend Strength Index
        trend_strength = min(100, abs(macd) * 10)
        signal.append(f"Trend Strength: {round(trend_strength)}")

        return {
            "Close Price": price,
            "SMA_50": round(sma_50, 2),
            "SMA_200": round(sma_200, 2) if sma_200 else None,
            "MACD": round(macd, 2),
            "Bollinger Band Range": [round(lower_band, 2), round(upper_band, 2)],
            "RSI": round(rsi, 2),
            "Trend Strength Index": round(trend_strength),
            "Signals": signal
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/refresh/all")
def refresh_all_stocks():
    return run_refresh()
    
    print(f"[CRON] Refresh triggered at {datetime.datetime.now()}")
    run_refresh()

def run_refresh():
    symbols = ["TATAMOTORS", "RELIANCE", "INFY", "HDFCBANK", "ITC", "SBIN", "LT"]
    refreshed = {}
    for symbol in symbols:
        try:
            print(f"[INFO] Fetching {symbol}...")
            data = fetch_screener_data(symbol)
            data["Technical Analysis"] = calculate_technical_analysis(data)
            refreshed[symbol] = data
            print(f"[SUCCESS] {symbol} fetched successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch {symbol}: {e}")
            refreshed[symbol] = {"error": str(e)}

    with open("screened_stocks.json", "w") as f:
        json.dump(refreshed, f, indent=2)

    return {"status": "success", "count": len(refreshed)}
