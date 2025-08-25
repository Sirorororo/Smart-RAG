from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import router as api_router
from app.utils.db_utils import init_db
from app.config import setup_logging
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Logging setup complete.")
    init_db()
    logger.info("Database initialized.")
    yield
    # Shutdown
    logger.info("Application shutdown.")

app = FastAPI(title="Ingestion Service", lifespan=lifespan)

# include routes
app.include_router(api_router, prefix="/api")
