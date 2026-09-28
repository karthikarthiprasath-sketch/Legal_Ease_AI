from fastapi import FastAPI
from backend.routes import router

app = FastAPI(
    title="LegalEase API",
    description="AI-powered legal document generation platform",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "application": "LegalEase",
        "status": "running",
        "message": "Welcome to LegalEase API",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }