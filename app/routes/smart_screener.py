from fastapi import APIRouter
import json
import os

router = APIRouter()

@router.get("/stocks")
def get_screened_stocks():
    try:
        file_path = "app/auto_results.json"
        if not os.path.exists(file_path):
            return {"error": "auto_results.json not found. Please run the screener first."}
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load stocks: {str(e)}"}
