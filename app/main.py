from fastapi import FastAPI
from api.routes import router as api_router

app = FastAPI(title="Ingestion Service")

# include routes
app.include_router(api_router, prefix="/api")
