import pytz
import sys
import base64
import os
from app.database import init_models
from app.dependencies import get_session
from app.models import File
from app.schemas import ScribeInput
from datetime import datetime
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, Response, Form
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update, cast, Date, union, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from transcribe_anything import transcribe
from app.config import settings
from app.database import async_session
import os
from fastapi import UploadFile

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FILES_DIR = "/skrybafiles"

@app.on_event("startup")
async def on_startup():
    await init_models()
    async with async_session() as db:
        await db.execute(delete(File))
        await db.commit()
    os.makedirs(FILES_DIR, exist_ok=True)

#scribe endpoint: model - to choose
@app.post("/scribe-file/{model}")
async def scribe_file(model: str, file: UploadFile, db: AsyncSession = Depends(get_session)):
    new_file = File()
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    os.makedirs(f"{FILES_DIR}/{new_file.id}", exist_ok=True)
    print(file.content_type) # debug
    # if file.content_type not in ["audio/mpeg", "audio/wav", "video/mp4", "application/pdf", "text/plain"]:
        # raise HTTPException(status_code=400, detail="Unsupported file type")
    path = f"{FILES_DIR}/{new_file.id}/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    transcribe(
        url_or_file=path,
        output_dir=f"{FILES_DIR}/{new_file.id}",
        task="transcribe",
        model=model,
        device=settings.device,
        hugging_face_token=settings.hf_token if settings.hf_token != "None" else None,
        other_args=["--batch-size", "16"], #"--flash", "True",
    )
    return {"id": new_file.id}

#todo: scribe-url