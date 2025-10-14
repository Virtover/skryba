import pytz
import sys
import base64
import os
from app.database import init_models
from app.dependencies import get_session
from app.models import File
from app.schemas import ScribeUrlInput
from datetime import datetime
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, Response, Form
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import zipfile
import tempfile
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
@app.post("/scribe-file/{model}/.zip")
async def scribe_file(model: str, file: UploadFile, db: AsyncSession = Depends(get_session)):
    new_file = File()
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    os.makedirs(f"{FILES_DIR}/{new_file.id}", exist_ok=True)
    path = f"{FILES_DIR}/{new_file.id}/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    output_dir = f"{FILES_DIR}/{new_file.id}"
    transcribe(
        url_or_file=path,
        output_dir=output_dir,
        task="transcribe",
        model=model,
        device=settings.device,
        hugging_face_token=settings.hf_token if settings.hf_token != "None" else None,
        other_args=["--batch-size", "16"], #"--flash", "True",
    )
    
    zip_filename = f"{file.filename}_transcription_results.zip"
    zip_path = f"{output_dir}/{zip_filename}"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                if filename != zip_filename:  # Don't include the zip file itself
                    file_path = os.path.join(root, filename)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=zip_filename,
        media_type='application/zip'
    )


@app.post("/scribe-url/{model}/.zip")
async def scribe_url(model: str, data: ScribeUrlInput, db: AsyncSession = Depends(get_session)):
    new_file = File()
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    output_dir = f"{FILES_DIR}/{new_file.id}"
    os.makedirs(output_dir, exist_ok=True)

    transcribe(
        url_or_file=data.url,
        output_dir=output_dir,
        task="transcribe",
        model=model,
        device=settings.device,
        hugging_face_token=settings.hf_token if settings.hf_token != "None" else None
    )

    zip_filename = f"transcription_results.zip"
    zip_path = f"{output_dir}/{zip_filename}"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                if filename != zip_filename:  # Don't include the zip file itself
                    file_path = os.path.join(root, filename)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
    
    return FileResponse(
        path=zip_path,
        filename=zip_filename,
        media_type='application/zip'
    )
