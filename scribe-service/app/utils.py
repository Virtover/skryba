import os
import zipfile
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.models import File
from app.dependencies import get_session
from app.config import settings
from transcribe_anything import transcribe
import threading
import torch
from transformers import pipeline, MBartForConditionalGeneration, MBart50TokenizerFast
from app.lang_codes import to_mbart50

summarizer = pipeline(
    "summarization", 
    model="agentlans/granite-3.3-2b-notetaker", 
    dtype=torch.bfloat16, 
    device_map="auto"
)

lang_classifier = pipeline(
    "text-classification", 
    model="papluca/xlm-roberta-base-language-detection"
)

translator = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
tt_tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
tt_tokenizer_lock = threading.Lock()

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


def translate_text(text: str, src_lang: str, tgt_lang: str, chunk_tokens: int = 256) -> str:
    """Translate text from source language to target language by chunking tokens.

    Splits the tokenized input into chunks of size `chunk_tokens` and translates
    each chunk independently to avoid hitting model token limits.
    """
    # Tokenize once under lock (tokenizer has mutable src_lang)
    with tt_tokenizer_lock:
        tt_tokenizer.src_lang = src_lang
        encoded = tt_tokenizer(text, return_tensors="pt", add_special_tokens=True)

    input_ids = encoded["input_ids"].squeeze(0)
    attention_mask = encoded["attention_mask"].squeeze(0)

    seq_len = input_ids.size(0)
    device = next(translator.parameters()).device if hasattr(translator, 'parameters') else torch.device('cpu')

    outputs: list[str] = []
    with torch.no_grad():
        for start in range(0, seq_len, chunk_tokens):
            end = min(start + chunk_tokens, seq_len)
            chunk_ids = input_ids[start:end].unsqueeze(0).to(device)
            chunk_mask = attention_mask[start:end].unsqueeze(0).to(device)
            generated_tokens = translator.generate(
                input_ids=chunk_ids,
                attention_mask=chunk_mask,
                forced_bos_token_id=tt_tokenizer.lang_code_to_id[tgt_lang],
                max_new_tokens=300
            )
            decoded = tt_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            outputs.append(decoded[0])

    return " ".join(outputs)


def scribe(
    url_or_file: str, 
    output_dir: str,
    summary_lang: str = "en_XX"
) -> None:
    """Scribe with the given parameters.
    
    Returns:
        Path to the summary file
    """
    transcribe(
        url_or_file=url_or_file,
        output_dir=output_dir,
        task="transcribe",
        model="large-v3",
        device=settings.device,
        # hugging_face_token=settings.hf_token if settings.hf_token != "None" else None, #poor speaker diarization
        other_args=["--batch-size", "16"]  # "--flash", "True"
    )
    text = open(f"{output_dir}/out.txt", "r").read()
    src_code, std_code = to_mbart50(lang_classifier(text[:300])[0]['label']), to_mbart50("en_XX")
    text_en = translate_text(text, src_lang=src_code, tgt_lang=std_code) if src_code != std_code else text
    chunk_size = 3072
    chunks = [f"<text>{text_en[i:i+chunk_size]}</text>" for i in range(0, len(text_en), chunk_size)]
    summaries = summarizer(chunks)
    summaries = ["##" + summary['summary_text'].split("##", 1)[-1] for summary in summaries]
    summary = "# Summary\n\n" + "\n\n".join(summaries)
    
    summary_lang_code = to_mbart50(summary_lang)
    if summary_lang_code != std_code:
        translated_summary = translate_text(summary, src_lang=std_code, tgt_lang=summary_lang_code)
        with open(f"{output_dir}/summary_{summary_lang_code}.md", "w") as f:
            f.write(translated_summary)

    with open(f"{output_dir}/summary.md", "w") as f:
        f.write(summary)


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
