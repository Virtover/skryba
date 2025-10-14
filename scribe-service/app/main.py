import os
from app.database import init_models
from app.dependencies import get_session
from app.models import File
from app.schemas import ScribeUrlInput
from fastapi import (
    BackgroundTasks, 
    FastAPI, 
    Depends, 
    UploadFile
)
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import zipfile
import tempfile
from sqlalchemy import select, update, cast, Date, union, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.utils import (
    create_file_record, 
    create_output_directory, 
    run_transcription, 
    create_zip_archive,
    save_uploaded_file,
    cleanup_resources,
    delete_file_safely
)
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


@app.post("/scribe-file/{model}/.zip")
async def scribe_file(
    model: str, 
    file: UploadFile, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    # Create database record and output directory
    new_file = await create_file_record(db)
    output_dir = create_output_directory(new_file.id, FILES_DIR)
    
    # Save uploaded file and run transcription
    file_content = await file.read()
    file_path = save_uploaded_file(file_content, file.filename, output_dir)
    run_transcription(file_path, output_dir, model)

    # Delete the uploaded file before zipping
    delete_file_safely(file_path)

    # Create and return zip file
    zip_filename = f"skryba-{new_file.id}_results"
    zip_path = create_zip_archive(output_dir, zip_filename)

    background_tasks.add_task(cleanup_resources, new_file.id, output_dir, db)

    return FileResponse(
        path=zip_path,
        filename=f"{zip_filename}.zip",
        media_type='application/zip'
    )


@app.post("/scribe-url/{model}/.zip")
async def scribe_url(
    model: str, 
    data: ScribeUrlInput, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    # Create database record and output directory
    new_file = await create_file_record(db)
    output_dir = create_output_directory(new_file.id, FILES_DIR)
    
    # Run transcription on URL
    run_transcription(data.url, output_dir, model)
    
    # Create and return zip file
    zip_filename = f"skryba-{new_file.id}_results"
    zip_path = create_zip_archive(output_dir, zip_filename)

    background_tasks.add_task(cleanup_resources, new_file.id, output_dir, db)
    
    return FileResponse(
        path=zip_path,
        filename=f"{zip_filename}.zip",
        media_type='application/zip'
    )
