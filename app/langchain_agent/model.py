import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env from project root
load_dotenv()


class ChatModelFactory:
    """Build the chat model used by the LangGraph agent."""

    def generator(self) -> Optional[ChatOpenAI]:
        api_key = os.getenv("API_KEY", "").strip()
        if not api_key:
            return None

        return ChatOpenAI(
            api_key=api_key,
            base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            model=os.getenv("OPENAI_MODEL", "qwen-plus"),
            temperature=0.2,
            max_tokens=3000,
            timeout=30,
            max_retries=2,
        )


def build_chat_model() -> ChatOpenAI:
    """Convenience wrapper for the rest of the app."""
    model = ChatModelFactory().generator()
    if model is None:
        raise ValueError("OPENAI_API_KEY is not set in .env")
    return model