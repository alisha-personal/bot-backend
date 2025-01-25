# server.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from lib.database import get_db, Base, engine
from lib.models import User, UserSession, Conversation
from lib.auth import (
    create_user, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    create_user_session
)
from lib.bot import create_tourism_bot, response_bot

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
    
    # Create user session
    session = create_user_session(db, user.id)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "session_id": session.id
    }

@app.post('/respond')
def get_response(
    data: Query, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate session_id if not provided
    session_id = data.session_id or str(uuid.uuid4())
    
    response = response_bot(
        llm=gemini_llm,
        system_prompt=system_prompt,
        query=data.query,
        session_id=session_id
    )
    
    # Save conversation to database
    conversation = Conversation(
        user_id=current_user.id,
        query=data.query,
        response=response
    )
    db.add(conversation)
    db.commit()
    
    return {
        "response": response,
        "session_id": session_id
    }