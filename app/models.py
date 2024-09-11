from pydantic import BaseModel
from typing import List, Optional


class AudioMetadata(BaseModel):
    id: Optional[int]
    src_id: str
    description: str
    audio_src: str
    location: str
    images: List[str]
    creators: List[str]
    tags: List[str]


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
