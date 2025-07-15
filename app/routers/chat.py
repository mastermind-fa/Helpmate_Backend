from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Set
from app.core.database import get_db
from app.models.chat import Chat, Message
from app.models.user import User
from app.models.worker import Worker
from app.schemas.chat import ChatCreate, ChatResponse, MessageCreate, MessageResponse, ChatListResponse
from app.routers.auth import get_current_user
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory mapping of chat_id to set of WebSocket connections
active_connections: Dict[int, Set[WebSocket]] = {}

async def broadcast_message(chat_id: int, message: dict):
    connections = active_connections.get(chat_id, set())
    to_remove = set()
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        connections.discard(ws)

@router.websocket("/ws/chat/{chat_id}")
async def websocket_chat(websocket: WebSocket, chat_id: int):
    await websocket.accept()
    if chat_id not in active_connections:
        active_connections[chat_id] = set()
    active_connections[chat_id].add(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Just keep alive, no direct send from client
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        active_connections[chat_id].discard(websocket)
        if not active_connections[chat_id]:
            del active_connections[chat_id]


@router.post("/", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat between user and worker"""
    # Verify the user is creating the chat
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can create chats"
        )
    
    # Check if worker exists
    worker = db.query(Worker).filter(Worker.id == chat.worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Check if chat already exists
    existing_chat = db.query(Chat).filter(
        Chat.user_id == current_user.id,
        Chat.worker_id == chat.worker_id,
        Chat.is_active == True
    ).first()
    
    if existing_chat:
        return existing_chat
    
    # Create new chat
    db_chat = Chat(
        user_id=current_user.id,
        worker_id=chat.worker_id
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


@router.get("/", response_model=List[ChatListResponse])
async def get_user_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chats for the current user"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access chats"
        )
    
    chats = db.query(Chat).filter(
        Chat.user_id == current_user.id,
        Chat.is_active == True
    ).all()
    
    result = []
    for chat in chats:
        # Get last message
        last_message = db.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(Message.created_at.desc()).first()
        
        # Get unread count
        unread_count = db.query(Message).filter(
            Message.chat_id == chat.id,
            Message.sender_type == "worker",
            Message.is_read == False
        ).count()
        
        chat_data = ChatListResponse(
            id=chat.id,
            user_id=chat.user_id,
            worker_id=chat.worker_id,
            is_active=chat.is_active,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            user=chat.user,
            worker=chat.worker,
            last_message=last_message,
            unread_count=unread_count
        )
        result.append(chat_data)
    
    return result


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat with messages"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access chats"
        )
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat


@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can send messages"
        )
    
    # Check if chat exists and user has access
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Create message
    db_message = Message(
        chat_id=chat_id,
        sender_type="user",
        sender_id=current_user.id,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    # Broadcast to WebSocket
    await broadcast_message(chat_id, MessageResponse.from_orm(db_message).dict())
    return db_message


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: int,
    current_user = Depends(get_current_user),  # Can be User or Worker
    db: Session = Depends(get_db)
):
    """Get all messages in a chat"""
    # Find the chat
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    # Check if current user/worker is a participant
    allowed = False
    if isinstance(current_user, User) and chat.user_id == current_user.id:
        allowed = True
    if isinstance(current_user, Worker) and chat.worker_id == current_user.id:
        allowed = True

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this chat's messages"
        )

    messages = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at.asc()).all()

    return messages


# Worker endpoints for chat
@router.get("/worker/chats", response_model=List[ChatListResponse])
async def get_worker_chats(
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chats for the current worker"""
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access chats"
        )
    
    chats = db.query(Chat).filter(
        Chat.worker_id == current_worker.id,
        Chat.is_active == True
    ).all()
    
    result = []
    for chat in chats:
        # Get last message
        last_message = db.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(Message.created_at.desc()).first()
        
        # Get unread count
        unread_count = db.query(Message).filter(
            Message.chat_id == chat.id,
            Message.sender_type == "user",
            Message.is_read == False
        ).count()
        
        chat_data = ChatListResponse(
            id=chat.id,
            user_id=chat.user_id,
            worker_id=chat.worker_id,
            is_active=chat.is_active,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            user=chat.user,
            worker=chat.worker,
            last_message=last_message,
            unread_count=unread_count
        )
        result.append(chat_data)
    
    return result


@router.post("/worker/{chat_id}/messages", response_model=MessageResponse)
async def send_worker_message(
    chat_id: int,
    message: MessageCreate,
    current_worker: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message as a worker"""
    if not isinstance(current_worker, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can send messages"
        )
    
    # Check if chat exists and worker has access
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.worker_id == current_worker.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Create message
    db_message = Message(
        chat_id=chat_id,
        sender_type="worker",
        sender_id=current_worker.id,
        content=message.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    # Broadcast to WebSocket
    await broadcast_message(chat_id, MessageResponse.from_orm(db_message).dict())
    return db_message


@router.put("/{chat_id}/messages/{message_id}/read")
async def mark_message_as_read(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can mark messages as read"
        )
    
    # Check if chat exists and user has access
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Mark message as read
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    message.is_read = True
    db.commit()
    return {"message": "Message marked as read"} 