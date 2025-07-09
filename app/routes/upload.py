from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def dummy_upload():
    return {"message": "Upload endpoint is under construction"}

