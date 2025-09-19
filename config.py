"""
Configuration management for the PRD Code Verifier application.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from models import AIProvider, AIProviderConfig

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Application settings
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "True").lower() == "true"
    
    # Default AI provider
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Gemini settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    
    # LM Studio settings
    LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
    
    @classmethod
    def get_default_ai_config(cls) -> AIProviderConfig:
        """Get default AI configuration based on environment variables."""
        provider = AIProvider(cls.DEFAULT_AI_PROVIDER)
        
        if provider == AIProvider.OPENAI:
            return AIProviderConfig(
                provider=provider,
                api_key=cls.OPENAI_API_KEY,
                base_url=cls.OPENAI_BASE_URL,
                model=cls.OPENAI_MODEL
            )
        elif provider == AIProvider.GEMINI:
            return AIProviderConfig(
                provider=provider,
                api_key=cls.GEMINI_API_KEY,
                model=cls.GEMINI_MODEL
            )
        elif provider == AIProvider.OLLAMA:
            return AIProviderConfig(
                provider=provider,
                base_url=cls.OLLAMA_BASE_URL,
                model=cls.OLLAMA_MODEL
            )
        elif provider == AIProvider.LM_STUDIO:
            return AIProviderConfig(
                provider=provider,
                base_url=cls.LM_STUDIO_BASE_URL,
                model=cls.LM_STUDIO_MODEL
            )
        else:
            # Fallback to OpenAI
            return AIProviderConfig(
                provider=AIProvider.OPENAI,
                api_key=cls.OPENAI_API_KEY,
                base_url=cls.OPENAI_BASE_URL,
                model=cls.OPENAI_MODEL
            )
