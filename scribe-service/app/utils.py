import os
import re
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


def srt_group_chunks(
    srt_path: str,
    group_size: int = 10,
) -> list[tuple[str, str]]:
    """Group SRT entries into chunks of size `group_size`.

    Returns:
        List of (timestamp, text) tuples. Each timestamp is "start --> end"
        from the first and last entries in the group. Text is concatenated
        from all entries in the group.
    """
    if group_size <= 0:
        raise ValueError("group_size must be positive")

    # Split on blank lines to get SRT blocks
    with open(srt_path, "r", encoding="utf-8") as f:
        blocks = re.split(r"\r?\n\s*\r?\n", f.read().strip())

    # Parse blocks into (start, end, text)
    entries: list[tuple[str | None, str | None, str]] = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln is not None]
        if len(lines) < 2:
            continue
        ts = lines[1].strip()
        start = end = None
        if "-->" in ts:
            start, end = [p.strip() for p in ts.split("-->", 1)]
        text = "\n".join(ln.rstrip() for ln in lines[2:] if ln.strip()).strip()
        entries.append((start, end, text))

    # Group consecutive entries
    chunks: list[tuple[str, str]] = []
    for i in range(0, len(entries), group_size):
        grp = entries[i:i + group_size]
        if not grp:
            continue
        merged_text = " ".join(t for _, _, t in grp if t)
        s0, _, _ = grp[0]
        _, eN, _ = grp[-1]
        timestamp = f"{s0 or ''} --> {eN or ''}".strip()
        chunks.append((timestamp, merged_text))

    return chunks


def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """Translate text from source language to target language.
    """
    with tt_tokenizer_lock:
        tt_tokenizer.src_lang = src_lang
        encoded = tt_tokenizer(text, return_tensors="pt", add_special_tokens=True)
    
    generated_tokens = translator.generate(
        **encoded,
        forced_bos_token_id=tt_tokenizer.lang_code_to_id[tgt_lang]
    )
    decoded = tt_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return decoded[0]


def translate_summary(
    summary: str,
    src_lang: str,
    tgt_lang: str,
) -> str:
    """Translate summary text line-by-line, skipping empty lines and fixing markdown.
    
    Post-processes to fix malformed bold markers like '** text **' -> '**text**'.
    """
    lines = summary.split("\n")
    non_empty = [line for line in lines if line.strip()]
    translated = [translate_text(line, src_lang=src_lang, tgt_lang=tgt_lang) for line in non_empty]
    tr_iter = iter(translated)
    result = "\n".join(next(tr_iter) if line.strip() else "" for line in lines)
    result = re.sub(r'\*\*\s+', '**', result)
    result = re.sub(r'\s+\*\*', '**', result)
    return result


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
    srt_chunks = srt_group_chunks(f"{output_dir}/out.srt", group_size=20)
    if len(srt_chunks) == 0:
        return
    print(srt_chunks)
    std_code = to_mbart50("en_XX")
    src_code = to_mbart50(
        lang_classifier(srt_chunks[0][1][:min(300, len(srt_chunks[0][1]))])[0]['label']
    )
    translated_chunks = [
        (ts, translate_text(text, src_lang=src_code, tgt_lang=std_code) 
         if src_code != std_code else text) for ts, text in srt_chunks
    ]
    print(translated_chunks)
    summary = summarizer(
        "<text>" + " ".join([text for _, text in translated_chunks]) + "</text>",
        min_new_tokens=0,
        max_new_tokens=131072,
    )[0]['summary_text'].split("</text>", 1)[-1].split("</notes>", 1)[0]
    print(summary)

    dst_code = to_mbart50(summary_lang)
    if dst_code != std_code:
        tr_summary = translate_summary(summary, src_lang=std_code, tgt_lang=dst_code)
        print(tr_summary)
        with open(f"{output_dir}/summary_{summary_lang}.md", "w", encoding="utf-8") as f:
            f.write(tr_summary)

    with open(f"{output_dir}/out_grouped.srt", "w", encoding="utf-8") as f:
        for i, (ts, text) in enumerate(srt_chunks, start=1):
            f.write(f"{i}\n{ts}\n{text}\n\n")

    with open(f"{output_dir}/summary_en.md", "w", encoding="utf-8") as f:
        f.write(summary)


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
