import json
from app.services.screener import get_screener_data
from app.services.nse import get_nse_data
from app.services.technical import get_technical_indicators
from app.services.filters import apply_filters
from app.services.ai_insight import generate_ai_insight

def run_auto_scan():
    with open("app/stocks_universe.txt", "r") as f:
        symbols = [line.strip().upper() for line in f.readlines()]

    results = []

    for symbol in symbols:
        screener = get_screener_data(symbol)
        nse = get_nse_data(symbol)
        technicals = get_technical_indicators(symbol)
        verdict = apply_filters(screener, nse, technicals)

        if verdict == "PASS":
            ai = generate_ai_insight(screener, nse, technicals).get("ai_insight")
            results.append({
                "stock": symbol,
                "verdict": verdict,
                "screener": screener,
                "nse": nse,
                "technicals": technicals,
                "ai_insight": ai
            })

    with open("app/auto_results.json", "w") as out:
        json.dump(results, out, indent=2)

if __name__ == "__main__":
    run_auto_scan()
