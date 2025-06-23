from fastapi import Depends, FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from aws.aws_route import aws_router
from db_connect import get_db
from sqlalchemy.orm import Session
from lucopay.lucopay import lucopay_router
from auth.authapp import auth_router, get_current_user
from sqlalchemy import text
import os
import httpx
from contextlib import asynccontextmanager
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_URL = os.environ.get("APP_URL", "https://luco_service.onrender.com")

PING_INTERVAL = 600

async def keep_alive():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                logger.info(f"Sending keep-alive ping to {APP_URL}/health")
                response = await client.get(f"{APP_URL}/health")
                logger.info(f"Keep-alive response: {response.status_code}")
            except Exception as e:
                logger.error(f"Keep-alive ping failed: {str(e)}")
            
            await asyncio.sleep(PING_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    task = asyncio.create_task(keep_alive())
    yield
    
    task.cancel()



app = FastAPI(lifespan=lifespan)



app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://lucosms-ui.vercel.app", "https://lucosms-ui.vercel.app"],
    # allow_origins=["http://localhost:5173", "http://localhost:5173/"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "online"
        db_error = None
    except Exception as e:
        db_status = "offline"
        db_error = str(e)

    return {
        "message": "You are connected.",
        "version": "1.1.0",
        "author": "Abaasa Albert",
        "status": db_status,
        "db_error": db_error
    }

app.include_router(aws_router)
app.include_router(lucopay_router)
app.include_router(auth_router)