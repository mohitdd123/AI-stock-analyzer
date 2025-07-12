from stock_engine import analyze_many_stocks, get_index

if __name__ == "__main__":
    symbols = get_index()
    print(f"📈 Running analysis on {len(symbols)} stocks...")
    analyze_many_stocks(symbols)
    print("✅ Analysis complete. Saved to top_ranked_stocks.json")