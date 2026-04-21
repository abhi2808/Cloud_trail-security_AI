"""
CloudTrail AI Investigator — FastAPI Application Entry Point.
Initializes the app, CORS, auth middleware, and router registration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes.query import router as query_router
from app.api.routes.auth import router as auth_router
from app.api.routes.accounts import router as accounts_router
from app.middleware.auth import AuthMiddleware
from app.db.mongodb import connect_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events — startup and shutdown."""
    # Startup
    await connect_db()
    logger.info("=" * 60)
    logger.info("🚀 CloudTrail AI Investigator — Starting Up")
    logger.info(f"   AWS Region     : {settings.aws_region}")
    logger.info(f"   AI Provider    : {settings.ai_provider}")
    logger.info(f"   Client URL     : {settings.client_url}")
    logger.info(f"   Server Port    : {settings.port}")
    logger.info("=" * 60)
    yield
    # Shutdown
    await close_db()
    logger.info("🛑 CloudTrail AI Investigator — Shutting Down")


# Create FastAPI application
app = FastAPI(
    title="CloudTrail AI Investigator",
    description="Natural language security investigation tool for AWS CloudTrail logs. "
                "Ask questions in plain English and get investigator-style answers instantly.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add authentication middleware FIRST (runs last due to reverse stack order)
app.add_middleware(AuthMiddleware)

# Add CORS middleware — must be added AFTER AuthMiddleware so it runs FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-App-Key", "Authorization"],
)

# Register API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts_router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(query_router, prefix="/api", tags=["CloudTrail Investigation"])
