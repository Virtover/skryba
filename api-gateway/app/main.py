import datetime
import httpx
import json
from app.config import settings
from app.utils import forward_file_request, forward_json_request
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

@app.post("/scribe-file") # tiny, small, base, medium, large, large-v2, large-v3
async def scribe_file(file: UploadFile):
    file_content = await file.read()
    file_tuple = (file.filename, file_content, file.content_type)
    return await forward_file_request("scribe-file", file_tuple)


@app.post("/scribe-url") # tiny, small, base, medium, large, large-v2, large-v3
async def scribe_url(data: Dict[str, Any]):
    return await forward_json_request("scribe-url", data)
