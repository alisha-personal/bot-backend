# bot.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
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

def create_tourism_bot(temperature: float = 0.7) -> Tuple[ChatGoogleGenerativeAI, str, ConversationManager]:
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
    
    conversation_manager = ConversationManager()
    
    return llm, system_prompt, conversation_manager

def response_bot(llm: ChatGoogleGenerativeAI, system_prompt: str, query: str, session_id: str, conversation_manager: ConversationManager) -> str:
    """
    Generate response while maintaining conversation history.
    """
    # Get recent conversation history
    recent_history = conversation_manager.get_recent_history(session_id)
    
    # Build messages with history
    messages = [HumanMessage(content=f"System: {system_prompt}")]
    
    # Add recent conversation history to context
    for conv in recent_history:
        messages.extend([
            HumanMessage(content=conv["query"]),
            AIMessage(content=conv["response"])
        ])
    
    # Add current query
    messages.append(HumanMessage(content=query))
    
    # Get response
    response = llm(messages).content
    
    # Save to history
    conversation_manager.add_conversation(session_id, query, response)
    
    return response