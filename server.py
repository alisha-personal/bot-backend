# server.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv, find_dotenv
import uuid

load_dotenv(find_dotenv())

class Query(BaseModel):
    query: str
    session_id: str = None

from lib.bot import create_tourism_bot, response_bot

gemini_llm, system_prompt, conversation_manager = create_tourism_bot()

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post('/respond')
async def get_response(data: Query):
    # Generate session_id if not provided
    session_id = data.session_id or str(uuid.uuid4())
    
    response = response_bot(
        llm=gemini_llm,
        system_prompt=system_prompt,
        query=data.query,
        session_id=session_id,
        conversation_manager=conversation_manager
    )
    
    return {
        "response": response,
        "session_id": session_id
    }