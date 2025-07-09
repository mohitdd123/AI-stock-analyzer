from fastapi import APIRouter
import json

router = APIRouter()

@router.get("/stocks")
def get_screened_stocks():
    with open("app/auto_results.json", "r") as f:
        data = json.load(f)
    return data
