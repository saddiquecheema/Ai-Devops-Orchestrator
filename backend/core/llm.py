"""
=============================================================================
backend/core/llm.py — LLM FACTORY
=============================================================================
Settings se credentials uthakar ChatGroq ka instance deta hai.
=============================================================================
"""

from langchain_groq import ChatGroq
from backend.core.config import settings

def get_llm():
    """
    Groq LLM ka instance return karta hai using global settings.
    """
    return ChatGroq(
        groq_api_key    = settings.groq_api_key,
        model_name      = settings.groq_model,
        temperature     = settings.llm_temperature,
        max_tokens      = settings.llm_max_tokens,
    )