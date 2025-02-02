# server.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import uuid
from datetime import datetime
from dotenv import find_dotenv, load_dotenv

from lib.database import get_db, Base, engine
from lib.models import User, ChatSession, Message
from lib.auth import (
    create_user, 
    authenticate_user, 
    create_access_token, 
    get_current_user
)
from lib.bot import create_tourism_bot, response_bot

load_dotenv(find_dotenv())
# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Gemini bot
gemini_llm, system_prompt= create_tourism_bot()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Request models
class UserRegistration(BaseModel):
    username: str
    email: str
    password: str

class Query(BaseModel):
    query: str
    session_id: Optional[str] = None

@app.get('/status')
def get_status():
    return {
        'status' : 'active'
    }

# Authentication routes
@app.post("/register")
def register_user(user: UserRegistration, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = (
        db.query(User)
        .filter((User.username == user.username) | (User.email == user.email))
        .first()
    )
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    new_user = create_user(
        db, 
        username=user.username, 
        email=user.email, 
        password=user.password
    )
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token({"sub": user.username})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_name": user.username  # Changed user_name to username for consistency
    }

class MessageResponse(BaseModel):
    content: str
    isBot: bool
    timestamp: datetime

class SessionResponse(BaseModel):
    session_name: str
    session_id: str
    last_message: datetime

class ConversationResponse(BaseModel):
    messages: List[MessageResponse]

@app.post('/respond')
async def get_response(
    data: Query,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = data.session_id
    query = data.query
    
    if not session_id:
        # Create new session
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            id=session_id,
            user_id=current_user.id,
            initial_message=query
        )
        db.add(chat_session)
    
    # Save user message
    user_message = Message(
        session_id=session_id,
        content=query,
        is_bot=False
    )
    db.add(user_message)
    
    # Get bot response
    bot_response = response_bot(
        llm=gemini_llm,
        system_prompt=system_prompt,
        query=query,
        session_id=session_id
    )
    
    # Save bot message
    bot_message = Message(
        session_id=session_id,
        content=bot_response,
        is_bot=True
    )
    db.add(bot_message)
    
    db.commit()
    
    return {
        "response": bot_response,
        "session_id": session_id
    }

@app.get("/user/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(
            ChatSession.id,
            ChatSession.initial_message,
            func.max(Message.timestamp).label('last_message')
        )
        .join(Message)
        .filter(ChatSession.user_id == current_user.id)
        .group_by(ChatSession.id, ChatSession.initial_message)
        .order_by(func.max(Message.timestamp).desc())
        .all()
    )
    
    return [
        SessionResponse(
            session_name=session.initial_message[:30] + "..." if len(session.initial_message) > 30 else session.initial_message,
            session_id=session.id,
            last_message=session.last_message
        )
        for session in sessions
    ]

@app.get("/user/sessions/{session_id}/messages", response_model=ConversationResponse)
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all messages for session
    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.timestamp)
        .all()
    )
    
    return ConversationResponse(
        messages=[
            MessageResponse(
                content=msg.content,
                isBot=msg.is_bot,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]
    )