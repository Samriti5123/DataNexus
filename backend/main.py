from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import upload_router, clean_router, eda_router, visualize_router, insights_router, export_router
from backend.services.data_service import DataService

app = FastAPI(
    title="DataLens API",
    description="Interactive Data Analysis & Business Intelligence Platform API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
    print(f"DataLens Backend initialized. Default session: {default_session.session_id} ({default_session.name})")

@app.get("/")
def root():
    return {
        "status": "online",
        "app": "DataLens – Interactive Data Analysis Platform",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
