from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from typing import Tuple

def create_tourism_bot(temperature: float = 0.7) -> Tuple[ChatGoogleGenerativeAI, str]:
    """
    Initialize Gemini with system prompt for Australian tourism assistance.
    
    Args:
        temperature (float): Temperature for response generation
        
    Returns:
        Tuple[ChatGoogleGenerativeAI, str]: Initialized chat model and system prompt
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

def response_bot(llm: ChatGoogleGenerativeAI, system_prompt: str, query: str) -> str:
    """
    Generate response for user query using the initialized Gemini model.
    
    Args:
        llm (ChatGoogleGenerativeAI): Initialized chat model
        system_prompt (str): System prompt defining bot behavior
        query (str): User's tourism-related query
        
    Returns:
        str: Bot's response
    """
    messages = [
        HumanMessage(content=f"System: {system_prompt}\n\nHuman: {query}")
    ]
    response = llm(messages)
    return response.content
