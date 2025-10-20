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
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy import select, update, cast, Date, union, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.utils import (
    create_file_record, 
    create_output_directory, 
    scribe, 
    create_zip_archive,
    save_uploaded_file,
    cleanup_resources,
    delete_file_safely,
    enable_tf32
)
from fastapi import UploadFile

FILES_DIR = "/skrybafiles"
enable_tf32()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    async with async_session() as db:
        await db.execute(delete(File))
        await db.commit()
    os.makedirs(FILES_DIR, exist_ok=True)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scribe-file")
async def scribe_file(
    file: UploadFile, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    new_file = await create_file_record(db)
    output_dir = create_output_directory(new_file.id, FILES_DIR)

    file_content = await file.read()
    file_path = save_uploaded_file(file_content, file.filename, output_dir)
    scribe(file_path, output_dir)

    delete_file_safely(file_path)
    zip_filename = f"skryba-{new_file.id}_results"
    zip_path = create_zip_archive(output_dir, zip_filename)

    background_tasks.add_task(cleanup_resources, new_file.id, output_dir, db)
    return FileResponse(
        path=zip_path,
        filename=f"{zip_filename}.zip",
        media_type='application/zip'
    )


@app.post("/scribe-url")
async def scribe_url(
    data: ScribeUrlInput, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    new_file = await create_file_record(db)
    output_dir = create_output_directory(new_file.id, FILES_DIR)
    scribe(data.url, output_dir)

    zip_filename = f"skryba-{new_file.id}_results"
    zip_path = create_zip_archive(output_dir, zip_filename)

    background_tasks.add_task(cleanup_resources, new_file.id, output_dir, db)
    return FileResponse(
        path=zip_path,
        filename=f"{zip_filename}.zip",
        media_type='application/zip'
    )
