from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from .user import UserResponse
from .worker import WorkerResponse


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    chat_id: int
    sender_type: str
    sender_id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        }


class ChatBase(BaseModel):
    worker_id: int


class ChatCreate(ChatBase):
    pass


class ChatResponse(ChatBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    worker: WorkerResponse
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        }


class ChatListResponse(BaseModel):
    id: int
    user_id: int
    worker_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    worker: WorkerResponse
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        } 