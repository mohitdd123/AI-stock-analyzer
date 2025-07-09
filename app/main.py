from fastapi import FastAPI
from app.routes.analysis import router as analysis_router
from app.routes.smart_screener import router as smart_router
from app.routes.upload import router as upload_router

app = FastAPI(title="AI Stock Screener")
app.include_router(analysis_router, prefix="/analyze")
app.include_router(upload_router, prefix="/upload")
app.include_router(smart_router, prefix="/screened")
