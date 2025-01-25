# bot.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from typing import Tuple, List, Dict
import json
from datetime import datetime
import os

class ConversationManager:
    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.conversations: Dict[str, List[Dict]] = self._load_history()
        
    def _load_history(self) -> Dict[str, List[Dict]]:
        """Load conversation history from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_history(self):
        """Save conversation history to JSON file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.conversations, f, indent=2)
            
    def add_conversation(self, session_id: str, query: str, response: str):
        """Add new conversation to history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response
        }
        
        self.conversations[session_id].append(conversation)
        
        # Keep only recent 3 conversations
        if len(self.conversations[session_id]) > 3:
            self.conversations[session_id] = self.conversations[session_id][-3:]
            
        self.save_history()
        
    def get_recent_history(self, session_id: str) -> List[Dict]:
        """Get recent conversation history for a session"""
        return self.conversations.get(session_id, [])

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

def response_bot(llm: ChatGoogleGenerativeAI, system_prompt: str, query: str, session_id: str) -> str:
    
    """
    Generate response using conversation context.
    """
    # Build messages with system prompt
    messages = [HumanMessage(content=f"System: {system_prompt}")]
    
    # Add current query
    messages.append(HumanMessage(content=query))
    
    # Get response
    response = llm(messages).content

    # Convert to HTML
    response = format_to_html(response, llm)
    
    return response

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