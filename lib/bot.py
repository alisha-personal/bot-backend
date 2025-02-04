# bot.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import PromptTemplate
from typing import Tuple, List, Dict
import json
from datetime import datetime
import os
from sqlalchemy.orm import Session
from .models import Message

def create_tourism_bot(temperature: float = 0.7) -> Tuple[ChatGoogleGenerativeAI, str]:
    """
    Initialize Gemini with system prompt and conversation manager.
    """
    system_prompt = """You are AussieGuide, an Australian tourism specialist. Focus areas:
- Australian destinations, attractions, and experiences only
- Natural landmarks, cities, cultural sites, and wildlife experiences
- Travel planning, timing, and practical advice
- Local customs, weather, and safety considerations
- Budgeting and accommodation recommendations

For non-Australian destinations: Politely explain you specialize in Australian travel only.

Provide clear, practical advice considering:
- Travel season and duration
- Budget and preferences
- Safety and accessibility
- Transport and accommodation options
Keep responses friendly, informative, and focused on Australian travel."""

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=temperature,
        convert_system_message_to_human=True
    )
    
    return llm, system_prompt

def validate_response(response: str, query: str, llm: ChatGoogleGenerativeAI) -> Tuple[bool, str]:
    """
    Validate if the response is related to Australian tourism and modify if needed.
    Returns: (is_valid, modified_response)
    """
    validator_prompt = """As an Australian tourism content validator, analyze the following query and response.
    Determine if the response is strictly related to Australian tourism, travel, or appropriately redirects non-Australian queries.
    
    Query: {query}
    Response: {response}
    
    If the response strays from Australian tourism or doesn't properly redirect non-Australian queries:
    1. Return "INVALID" on the first line
    2. Provide a corrected response focused on Australian tourism or a polite redirect
    
    If the response is appropriate:
    1. Return "VALID" on the first line
    2. Return the original response unchanged
    
    Your response should start with either VALID or INVALID on its own line, followed by the response text.
    """
    
    validation_prompt = PromptTemplate(
        template=validator_prompt,
        input_variables=["query", "response"]
    )
    
    validation_chain = validation_prompt | llm
    validation_result = validation_chain.invoke({
        "query": query,
        "response": response
    }).content
    
    # Split result into validation status and response
    lines = validation_result.split('\n', 1)
    is_valid = lines[0].strip() == "VALID"
    
    # Get the validated/corrected response
    validated_response = lines[1].strip() if len(lines) > 1 else response
    
    return is_valid, validated_response

def response_bot(
    llm: ChatGoogleGenerativeAI, 
    system_prompt: str, 
    query: str, 
    session_id: str,
    db: Session
) -> str:
    """
    Generate response using conversation context with validation.
    """
       # Get conversation history from database
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp.asc()).all()

    # Convert database messages to LangChain schema
    chat_history = []
    for msg in messages:
        if msg.is_bot:
            chat_history.append(AIMessage(content=msg.content))
        else:
            chat_history.append(HumanMessage(content=msg.content))

    # Build message chain with system prompt and history
    messages = [
        SystemMessage(content=system_prompt),  # Converted to human message by LLM setting
        *chat_history,
        HumanMessage(content=query)
    ]

    # Get initial response
    initial_response = llm(messages).content

    # Validate and potentially modify the response
    is_valid, validated_response = validate_response(initial_response, query, llm)

    # If not valid, retry with correction notice and full history
    if not is_valid:
        correction_messages = [
            SystemMessage(content=system_prompt + "\nIMPORTANT: Previous response was invalid. "
                            "You MUST focus on Australian tourism or redirect appropriately."),
            *chat_history,
            HumanMessage(content=query),
            HumanMessage(content="Please correct your response to focus on Australian tourism")
        ]
        validated_response = llm(correction_messages).content

    return format_to_html(validated_response, llm)

def format_to_html(text: str, llm: ChatGoogleGenerativeAI) -> str:
    template_post = """
You are an expert in transforming plain text into well-structured, visually appealing HTML content suitable for direct integration into a webpage. 

When formatting your response, use the following HTML tags:
- Use `<div></div>` for the overall container.
- Use `<p>` for paragraphs and `<h3>` for headings.
- Use `<ul>` or `<ol>` for unordered or ordered lists, and `<li>` for individual list items.
- Use `<strong>` to highlight key terms or emphasize technical concepts.
- For links, use `<a href="URL" target="_blank">Click Here</a>`.
- Use `<span>` for displaying numbers, statistics, or special data.

Please convert the following text into HTML: {query}

Your response should contain only HTML code—no additional syntax like ` ```html []` . 
    """
    
    html_prompt = PromptTemplate(
        template=template_post,
        input_variables=["query"]
    )
    
    html_chain = html_prompt | llm
    return html_chain.invoke({"query": text}).content