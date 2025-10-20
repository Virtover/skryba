import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.config import settings
from typing import Dict, Any, Union


async def forward_file_request(
    endpoint: str,
    file_tuple: tuple,
    timeout: Union[int, None] = None
) -> StreamingResponse:
    """Forward a file upload request to the scribe service and stream the response.
    
    Args:
        endpoint: The endpoint path (e.g., 'scribe-file')
        file_tuple: Tuple of (filename, content, content_type)
        timeout: Request timeout in seconds
    
    Returns:
        StreamingResponse with the file from scribe-service
    """
    async with httpx.AsyncClient() as client:
        files = {"file": file_tuple}
        response = await client.post(
            f"{settings.scribe_service_url}/{endpoint}", 
            files=files, 
            timeout=timeout
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return _create_streaming_response(response)


async def forward_json_request(
    model: str,
    endpoint: str,
    data: Dict[str, Any],
    timeout: Union[int, None] = None
) -> StreamingResponse:
    """Forward a JSON request to the scribe service and stream the response.
    
    Args:
        model: The model name (e.g., 'large-v3')
        endpoint: The endpoint path (e.g., 'scribe-url')
        data: JSON data to send
        timeout: Request timeout in seconds
    
    Returns:
        StreamingResponse with the file from scribe-service
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.scribe_service_url}/{endpoint}/{model}", 
            json=data, 
            timeout=timeout
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return _create_streaming_response(response)


def _create_streaming_response(response: httpx.Response) -> StreamingResponse:
    """Create a StreamingResponse from an httpx Response, preserving headers.
    
    Args:
        response: The httpx Response object
    
    Returns:
        StreamingResponse with proper headers
    """
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