from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.smart_screener import router as smart_router

app = FastAPI(title="AI Stock Screener")

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-stock-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "Backend is alive"}

app.include_router(smart_router, prefix="/screened")
