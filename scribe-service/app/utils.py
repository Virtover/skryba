import os
import zipfile
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models import File
from app.dependencies import get_session
from app.config import settings
from transcribe_anything import transcribe
import torch
from transformers import pipeline, M2M100ForConditionalGeneration, M2M100Tokenizer

summarizer = pipeline(
    "summarization", 
    model="agentlans/granite-3.3-2b-notetaker", 
    dtype=torch.bfloat16, 
    device_map="auto"
)

text_translator = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
tt_tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
tt_tokenizer.src_lang = "en"

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
    summary_lang: str = "en"
) -> str:
    """Scribe with the given parameters.
    
    Returns:
        Path to the summary file
    """
    summary_path = f"{output_dir}/summary_{summary_lang}.md"
    transcribe(
        url_or_file=url_or_file,
        output_dir=output_dir,
        task="translate",
        language="en",
        model="large-v3",
        device=settings.device,
        # hugging_face_token=settings.hf_token if settings.hf_token != "None" else None, #poor speaker diarization
        other_args=["--batch-size", "16"]  # "--flash", "True"
    )
    text = open(f"{output_dir}/out.txt", "r").read()
    adjusted_text = f"<text>{text}</text>"
    chunk_size = 3000
    chunks = [adjusted_text[i:i+chunk_size] for i in range(0, len(adjusted_text), chunk_size)]
    summaries = summarizer(chunks)
    summaries = ["##" + summary['summary_text'].split("##", 1)[1] for summary in summaries]
    warning = "WARNING: There may be errors because of translating between languages.\n\n"
    summary = warning + "# Study Notes\n\n" + "\n\n".join(summaries)
    # if summary_lang != "en":
    #     encoded = tt_tokenizer(summary, return_tensors="pt")
    #     print(encoded)
    #     generated_tokens = text_translator.generate(**encoded, forced_bos_token_id=tt_tokenizer.get_lang_id(summary_lang))
    #     summary = tt_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    #     print(summary)
    #     summary = summary[0]
    
    with open(summary_path, "w") as f:
        f.write(summary)

    return summary_path


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
