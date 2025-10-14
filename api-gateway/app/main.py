import datetime
import httpx
import json
from app.config import settings
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scribe-file/{model}/.zip") # tiny, small, base, medium, large, large-v2, large-v3
async def scribe_file(model: str, file: UploadFile):
    file_content = await file.read()
    async with httpx.AsyncClient() as client:
        files = {
            "file": (file.filename, file_content, file.content_type)
        }
        response = await client.post(
            f"{settings.scribe_service_url}/scribe-file/{model}/.zip", 
            files=files, 
            timeout=None
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        headers = {}
        content_disposition = response.headers.get("content-disposition")
        if content_disposition:
            headers["content-disposition"] = content_disposition
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/octet-stream"),
            headers=headers
        )

#todo: scribe-url
@app.post("/scribe-url/{model}/.zip") # tiny, small, base, medium, large, large-v2, large-v3
async def scribe_url(model: str, data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.scribe_service_url}/scribe-url/{model}/.zip", 
            json=data, 
            timeout=None
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        headers = {}
        content_disposition = response.headers.get("content-disposition")
        if content_disposition:
            headers["content-disposition"] = content_disposition
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/octet-stream"),
            headers=headers
        )
