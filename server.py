from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from lib.data import Query
from lib.bot import create_tourism_bot, response_bot

gemini_llm, system_prompt = create_tourism_bot()

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post('/respond')
async def get_response(data:Query):
    response = response_bot(
        llm = gemini_llm,
        system_prompt=system_prompt,
        query = data.query
    )
    return {
        "response" : response
    }
