import datetime
import httpx
import json
from app.config import settings
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Response, UploadFile, Form
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

@app.post("/scribe-file/{model}") # tiny, small, base, medium, large, large-v2, large-v3
async def scribe_file(model: str, file: UploadFile):
    file_content = await file.read()
    async with httpx.AsyncClient() as client:
        files = {
            "file": (file.filename, file_content, file.content_type)
        }
        response = await client.post(
            f"{settings.scribe_service_url}/scribe-file/{model}", 
            files=files, 
            timeout=None
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

#todo: scribe-url