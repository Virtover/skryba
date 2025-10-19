import os
import zipfile
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models import File
from app.dependencies import get_session
from app.config import settings
from transcribe_anything import transcribe
from textsum.summarize import Summarizer
import torch

summarizer = Summarizer(model_name_or_path='pszemraj/long-t5-tglobal-base-16384-book-summary')
# pszemraj/long-t5-tglobal-xl-16384-book-summary is too large for available memory

def enable_tf32():
    """Enable TF32 precision for matmul and cudnn (for Ampere+ GPUs)."""
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    try:
        torch.set_float32_matmul_precision('high')
    except AttributeError:
        pass


async def create_file_record(db: AsyncSession) -> File:
    """Create a new file record in the database and return it."""
    new_file = File()
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file


def create_output_directory(file_id: int, base_dir: str = "/skrybafiles") -> str:
    """Create and return the output directory path for a file."""
    output_dir = f"{base_dir}/{file_id}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def scribe(
    url_or_file: str, 
    output_dir: str, 
    model: str, 
    file_id: int,
    task: str = "transcribe",
) -> None:
    """Scribe with the given parameters."""
    transcribe(
        url_or_file=url_or_file,
        output_dir=output_dir,
        task=task,
        model=model,
        device=settings.device,
        # hugging_face_token=settings.hf_token if settings.hf_token != "None" else None, #poor speaker diarization
        other_args=["--batch-size", "16"]  # "--flash", "True"
    )
    out_path = f"{output_dir}/out{file_id}.txt"
    os.rename(f"{output_dir}/out.txt", out_path)
    summary_path = summarizer.summarize_file(out_path)
    shutil.move(summary_path, f"{output_dir}/summary.txt")


def create_zip_archive(output_dir: str, zip_filename: str) -> str:
    """Create a zip archive of all files in the output directory.
    
    Args:
        output_dir: Directory containing files to zip
        zip_filename: Name for the zip file (without .zip extension)
    
    Returns:
        Path to the created zip file
    """
    zip_path = f"{output_dir}/{zip_filename}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for filename in files:
                # Don't include zip files themselves to avoid recursion
                if not filename.endswith('.zip'):
                    file_path = os.path.join(root, filename)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
    
    return zip_path


async def cleanup_resources(file_id: int, output_dir: str, db: AsyncSession) -> None:
    """Clean up output directory and database record.
    
    This is typically called as a background task after serving the response.
    """
    try:
        # Delete the output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        # Delete the database record
        await db.execute(delete(File).where(File.id == file_id))
        await db.commit()
    except Exception as e:
        print(f"Cleanup error for file {file_id}: {e}")


def save_uploaded_file(file_content: bytes, filename: str, output_dir: str) -> str:
    """Save uploaded file content to the output directory.
    
    Returns:
        Path to the saved file
    """
    file_path = f"{output_dir}/{filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path

def delete_file_safely(file_path: str):
    """Delete a file, printing a warning if it fails."""
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Warning: could not delete uploaded file {file_path}: {e}")
