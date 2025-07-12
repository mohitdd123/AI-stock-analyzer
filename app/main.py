from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.stock_engine import get_analysis, get_index, search_symbols, get_top

api = FastAPI()
api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@api.get("/api/analyze/{symbol}")
def analyze(symbol: str):
    return get_analysis(symbol)

@api.get("/api/index")
def index():
    return get_index()

@api.get("/api/search")
def search(q: str = ""):
    return search_symbols(q)

@api.get("/api/top")
def top():
    return get_top()