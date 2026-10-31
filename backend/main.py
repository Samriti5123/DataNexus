import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import upload_router, clean_router, eda_router, visualize_router, insights_router, export_router
from backend.services.data_service import DataService

app = FastAPI(
    title="DataNexus API",
    description="Interactive Data Analysis & Business Intelligence Platform API",
    version="1.0.0"
)

# CORS configuration: securely allow configured frontend development origins
cors_env = os.environ.get("CORS_ORIGINS", "")
if cors_env:
    allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload_router.router)
app.include_router(clean_router.router)
app.include_router(eda_router.router)
app.include_router(visualize_router.router)
app.include_router(insights_router.router)
app.include_router(export_router.router)

@app.on_event("startup")
def startup_event():
    # Pre-populate sample session for instantaneous quick start
    default_session = DataService.load_sample_dataset("superstore_sales")
    print(f"DataNexus Backend initialized. Default session: {default_session.session_id} ({default_session.name})")

@app.get("/")
def root():
    return {
        "status": "online",
        "app": "DataNexus – Interactive Data Analysis Platform",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/health")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "DataNexus",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)
