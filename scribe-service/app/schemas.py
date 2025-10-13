from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, Union, Dict

class ScribeInput(BaseModel):
    is_file: bool
    url: Optional[str] = None
    content: Optional[UploadFile] = None
    model: Optional[str] = "large-v3"
