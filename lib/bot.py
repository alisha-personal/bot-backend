from langchain_google_genai import ChatGoogleGenerativeAI

def bot(llm):
    message = llm.invoke('what is the weather in australia?')
    return message.content