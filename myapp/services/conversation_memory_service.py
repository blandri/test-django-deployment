# conversation-memory.py

from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from typing import List
from .groq_service import GroqApi


class GroqLLM:
    """Adapter to make GroqApi work with LangChain memory/chain."""

    def __init__(self):
        self.groq_api = GroqApi()

    def predict(self, messages: List[BaseMessage]) -> str:
        """
        Emulates LangChain LLM interface.
        Takes a list of messages and returns Groq response.
        """
        # Convert messages into a single prompt
        prompt = ""
        for m in messages:
            if isinstance(m, HumanMessage):
                prompt += f"User: {m.content}\n"
            elif isinstance(m, AIMessage):
                prompt += f"Assistant: {m.content}\n"

        return self.groq_api.callGroq(prompt)


class ConversationMemoryAgent:
    def __init__(self):
        # --- Wrap your Groq API in LangChain-compatible class ---
        self.groq_api = GroqApi()
        self.llm = GroqLLM()

        # --- Initialize short-term memory ---
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def chat(self, user_input: str) -> str:
        # Collect history
        messages = self.memory.chat_memory.messages
        messages.append(HumanMessage(content=user_input))

        # Get response from Groq via wrapper
        response = self.llm.predict(messages)

        # Save to memory
        messages.append(AIMessage(content=response))

        return response
    
    def add_interaction(self, user_input: str, ai_output: str) -> None:
        self.memory.chat_memory.add_message(HumanMessage(content=user_input))
        self.memory.chat_memory.add_message(AIMessage(content=ai_output))

    def get_history(self) -> List[BaseMessage]:
        return list(self.memory.chat_memory.messages)

    def reset_memory(self):
        self.memory.clear()

    def get_last_ai_response(self) -> str:
        """Fetch the last assistant response only."""
        messages = self.memory.chat_memory.messages
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
        return ""
