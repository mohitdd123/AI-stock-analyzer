from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analysis import router as analysis_router
from app.routes.smart_screener import router as smart_router
from app.routes.upload import router as upload_router

app = FastAPI(title="AI Stock Screener")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ai-stock-frontend.vercel.app"],  # ✅ Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analysis_router, prefix="/analyze")
app.include_router(upload_router, prefix="/upload")
app.include_router(smart_router, prefix="/screened")
