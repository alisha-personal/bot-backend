from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from lib.data import Query
from lib.bot import bot

gemini_llm = ChatGoogleGenerativeAI(
    model = "gemini-1.5-flash"
)

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get('/respond')
async def respond():
    response = bot(gemini_llm)
    return {
        'response' : response
    }
