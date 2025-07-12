# PHASE 1: Core backend financial engine
# File: stock_engine.py

import requests
from bs4 import BeautifulSoup
import yfinance as yf
import math

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.9',
}

def safe_float(x):
    try:
        return float(x.replace(',', '').replace('%', ''))
    except:
        return 0.0

# ---------------------------
# Screener financial crawler
# ---------------------------
def scrape_screener(symbol):
    url = f"https://www.screener.in/company/{symbol}/"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = {
        "name": soup.select_one(".company-header .flex h1").text.strip() if soup.select_one(".company-header h1") else symbol,
        "sector": soup.select_one(".about .sub") and soup.select_one(".about .sub").text.strip().split('\n')[0],
        "peg": None,
        "roe": None,
        "holdings": {},
        "peers": [],
        "financials": {
            "Revenue": {},
            "Profit": {},
            "EPS": {},
        }
    }

    # PEG, ROE
    for r in soup.select(".company-ratios span.name"):
        label = r.text.strip()
        val = r.find_next_sibling("span")
        if label == "PEG Ratio" and val:
            data["peg"] = safe_float(val.text.strip())
        if label == "Return on equity" and val:
            data["roe"] = safe_float(val.text.strip())

    # Holdings
    holding_table = soup.find("section", id="holdings")
    if holding_table:
        for row in holding_table.select("tbody tr"):
            cols = row.select("td")
            if len(cols) >= 2:
                data["holdings"][cols[0].text.strip()] = cols[1].text.strip()

    # Peers
    peer_section = soup.find("section", id="peers")
    if peer_section:
        for row in peer_section.select("tbody tr"):
            cells = [td.text.strip() for td in row.select("td")]
            if cells:
                data["peers"].append(cells)

    # Revenue, PAT, EPS (Profit & Loss section)
    pl_section = soup.find("section", {"id": "profit-loss"})
    if pl_section:
        headers = [th.text.strip() for th in pl_section.select("thead tr th")]
        rows = pl_section.select("tbody tr")
        for row in rows:
            label = row.select_one("td").text.strip()
            values = [td.text.strip().replace(',', '') for td in row.select("td")[1:]]
            if "Revenue" in label:
                data["financials"]["Revenue"] = dict(zip(headers[1:], values))
            if "Net Profit" in label:
                data["financials"]["Profit"] = dict(zip(headers[1:], values))
            if "EPS" in label:
                data["financials"]["EPS"] = dict(zip(headers[1:], values))

    return data

# ---------------------------
# CAGR calculator
# ---------------------------
def calc_cagr(start_val, end_val, years):
    try:
        return round(((end_val / start_val) ** (1 / years) - 1) * 100, 2)
    except:
        return None

# ---------------------------
# Intrinsic value via DCF
# ---------------------------
def calc_intrinsic_value(current_eps, growth_rate, pe_ratio, years=5):
    try:
        future_eps = current_eps * ((1 + growth_rate / 100) ** years)
        future_price = future_eps * pe_ratio
        return round(future_price / ((1 + 0.12) ** years), 2)
    except:
        return None

# ---------------------------
# Historical price CAGR
# ---------------------------
def get_price_cagr(symbol):
    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period="5y")
        start = hist['Close'].iloc[0]
        end = hist['Close'].iloc[-1]
        return calc_cagr(start, end, 5)
    except:
        return None

# ---------------------------
# ---------------------------
# ChatGPT Investment Summary
# ---------------------------
import os
import openai

def get_ai_summary(data):
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        prompt = f"""
        Analyze the following stock:

        Name: {data.get('name')}
        Sector: {data.get('sector')}
        ROE: {data.get('roe')}
        PEG: {data.get('peg')}
        EPS CAGR: {data.get('cagr_eps')}
        Price CAGR: {data.get('price_cagr')}
        Intrinsic Value: {data.get('intrinsic_value')}
        Tags: {', '.join(data.get('classification', []))}
        Sentiment: {data.get('sentiment')}

        Based on this data, write a detailed investment analysis including:
        1. Strengths and weaknesses
        2. Growth outlook
        3. Risk factors
        4. Investment recommendation
        5. A final conclusion in one sentence
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI analysis unavailable: {e}"

# ---------------------------
# NSE Order Book Fetch
# ---------------------------
def fetch_nse_orderbook(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com"
        }
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            order_data = {
                "priceInfo": json_data.get("priceInfo", {}),
                "orderBook": json_data.get("marketDeptOrderBook", {})
            }
            return order_data
        else:
            return {"error": f"NSE API response {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ---------------------------
# Inject order book and GPT summary into full analyzer
# ---------------------------
def analyze_stock(symbol):
    base = scrape_screener(symbol)

    try:
        eps_data = base['financials']['EPS']
        years = list(eps_data.keys())[-5:]
        eps_vals = [safe_float(eps_data[y]) for y in years if eps_data[y]]
        if len(eps_vals) >= 2:
            cagr = calc_cagr(eps_vals[0], eps_vals[-1], len(eps_vals) - 1)
            intrinsic = calc_intrinsic_value(eps_vals[-1], cagr, pe_ratio=base['peg'] * base['roe'] if base['peg'] and base['roe'] else 15)
        else:
            cagr = intrinsic = None
    except:
        cagr = intrinsic = None
        years = []

    chart_labels = years
    chart_revenue = [safe_float(base['financials']['Revenue'].get(y, 0)) for y in years]
    chart_profit = [safe_float(base['financials']['Profit'].get(y, 0)) for y in years]
    chart_eps = [safe_float(base['financials']['EPS'].get(y, 0)) for y in years]

    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period="5y")
        valuation_chart = {
            "years": [str(d.year) for d in hist.index[-5::52]],
            "price": [round(p, 2) for p in hist['Close'][-5::52]],
            "intrinsic": [intrinsic for _ in range(5)]
        }
    except:
        valuation_chart = {"years": [], "price": [], "intrinsic": []}

    result = {
        "symbol": symbol,
        "name": base["name"],
        "sector": base["sector"],
        "peg": base["peg"],
        "roe": base["roe"],
        "holdings": base["holdings"],
        "peers": base["peers"],
        "cagr_eps": cagr,
        "price_cagr": get_price_cagr(symbol),
        "intrinsic_value": intrinsic,
        "financials": base["financials"],
        "financials_chart": {
            "labels": chart_labels,
            "revenue": chart_revenue,
            "profit": chart_profit,
            "eps": chart_eps
        },
        "valuation_chart": valuation_chart,
        "peer_table": base["peers"],
        "holding_structure": base["holdings"]
    }

    result["classification"] = classify_stock(result)
    result["sentiment"] = analyze_sentiment(result)
    result["ai_summary"] = get_ai_summary(result)
    try:
        result["nse_orderbook"] = fetch_nse_orderbook(symbol)
    except Exception as e:
        result["nse_orderbook"] = {"error": f"NSE fetch failed: {str(e)}"}

    return result

# ---------------------------
# FastAPI App and Endpoints
# ---------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
def root():
    return {"status": "Backend is live"}

@api.get("/api/analyze/{symbol}")
def analyze(symbol: str):
    try:
        data = analyze_stock(symbol.upper())
        return data
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

# ---------------------------
# Sentiment and classification engine
# ---------------------------
def classify_stock(data):
    tags = []
    if data.get("peg") is not None and data.get("roe") is not None and data["peg"] < 1 and data["roe"] > 18:
        tags.append("Multibagger")
    if data.get("peg") is not None and data.get("roe") is not None and data["peg"] < 2 and data["roe"] > 20:
        tags.append("Quality Pick")
    if data.get("cagr_eps") is not None and data["cagr_eps"] > 20:
        tags.append("High Growth")
    return tags

def analyze_sentiment(data):
    score = 0
    if data.get("roe") is not None and data["roe"] > 18: score += 1
    if data.get("peg") is not None and data["peg"] < 1.5: score += 1
    if data.get("cagr_eps") is not None and data["cagr_eps"] > 15: score += 1
    if data.get("price_cagr") is not None and data["price_cagr"] > 15: score += 1
    if score >= 3:
        return "Positive"
    elif score == 2:
        return "Neutral"
    else:
        return "Negative"
