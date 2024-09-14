from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AudioMetadata(BaseModel):
    src_id: str
    description: str
    audio_src: str
    location: str
    images: List[str]
    creator: str
    tags: List[str]
    created_at: datetime


class Creator(BaseModel):
    id: Optional[int]
    creator_id: str


class Tag(BaseModel):
    id: Optional[int]
    name: str


class UserInteraction(BaseModel):
    user_id: str
    src_id: str
    is_fav: bool
    viewed: bool
    finished: bool
    listened_second: int
    listened_percentage: float
    bookmarks: List[str]
    comments: List[str]
    recommended: bool


class User(BaseModel):
    id: int
    openid: str
    session_key: str
    created_at: datetime
    # Add other necessary fields here
