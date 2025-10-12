import datetime

from app.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
