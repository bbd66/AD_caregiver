from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import pymysql
import os
from pathlib import Path

from api.routes import api_router
from core.config import settings
from middleware.logging import logging_middleware
from db.db_digital_manage import DatabaseManager
from services.register_service import RegisterService
from services.login_service import LoginService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("main")

# Ensure database exists
def ensure_database_exists():
    try:
        # Connect without specifying database name
        conn = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset=settings.DB_CHARSET
        )
        
        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{settings.DB_NAME}'")
            if not cursor.fetchone():
                logger.info(f"Database {settings.DB_NAME} does not exist, creating...")
                cursor.execute(f"CREATE DATABASE {settings.DB_NAME} CHARACTER SET {settings.DB_CHARSET}")
                logger.info(f"Database {settings.DB_NAME} created successfully")
            else:
                logger.info(f"Database {settings.DB_NAME} already exists")
                
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error ensuring database exists: {e}", exc_info=True)
        return False

# Ensure static directories exist
def ensure_static_dirs():
    """Ensure static directories exist"""
    static_dirs = [
        "static",
        "static/audio",
        "static/images",
        "static/uploads",
        "static/uploads/avatars",
        "static/uploads/digital_humans",
        "static/uploads/digital_humans/documents"
    ]
    
    for dir_path in static_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

app = FastAPI(
    title=settings.APP_NAME,
    description="Digital Human Caregiver API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(logging_middleware)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize DatabaseManager
db_manager = DatabaseManager(
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    db=settings.DB_NAME,
    port=settings.DB_PORT,
    charset=settings.DB_CHARSET
)

# Initialize services
register_service = RegisterService(db_manager)
login_service = LoginService(db_manager)

# Include routers
app.include_router(api_router)

@app.on_event("startup")
async def startup_db_client():
    """Ensure database exists and static directories are created when the application starts"""
    logger.info("Checking database...")
    ensure_database_exists()
    logger.info("Checking static directories...")
    ensure_static_dirs()
    logger.info("Connecting to database...")
    db_manager.connect()  # Connect to the database on startup

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection when the application shuts down"""
    logger.info("Closing database connection...")
    db_manager.disconnect()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)