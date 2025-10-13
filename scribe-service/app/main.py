import pytz
import sys
import base64
from app.database import init_models
from app.dependencies import get_session
from app.models import File
from datetime import datetime
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update, cast, Date, union, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from transcribe_anything import transcribe
from app.config import settings
from app.database import async_session

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_models()
    async with async_session() as db:
        await db.execute(delete(File))
        await db.commit()
    transcribe(
        url_or_file="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        output_dir="/skryba_results",
        task="transcribe",
        model="large-v3",
        device=settings.device,
        hugging_face_token=settings.hf_token if settings.hf_token != "None" else None,
        other_args=["--batch-size", "16"], #"--flash", "True", 
    ) # test

#scribe endpoint: model - to choose