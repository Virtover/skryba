from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, Union, Dict


class LoadMoreInput(BaseModel):
    amount: int
    offset: int


class MessageInput(BaseModel):
    sender: str
    date: datetime
    isFile: bool
    content: Union[str, UploadFile]
    filename: Optional[str] = None


class MessageOutput(BaseModel):
    id: int
    sender: str
    date: datetime
    isFile: bool
    content: Union[str, Dict[str, Union[str, int]]]


class LoadMoreOutput(BaseModel):
    messages: list[MessageOutput]
