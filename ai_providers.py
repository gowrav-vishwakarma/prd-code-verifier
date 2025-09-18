"""
AI provider implementations for different LLM services.
"""

import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import openai
import google.generativeai as genai
import ollama
from models import AIProviderConfig, AIProvider


class BaseAIProvider(ABC):
    """Base class for AI providers."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the AI provider."""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    async def generate_response(self, prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model)
    
    async def generate_response(self, prompt: str) -> str:
        """Generate response using Gemini API."""
        try:
            # Run the synchronous Gemini call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config.temperature,
                        max_output_tokens=self.config.max_tokens
                    )
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


class OllamaProvider(BaseAIProvider):
    """Ollama local provider."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = ollama.AsyncClient(host=config.base_url or "http://localhost:11434")
    
    async def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            response = await self.client.generate(
                model=self.config.model,
                prompt=prompt,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            )
            return response["response"]
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")


class LMStudioProvider(BaseAIProvider):
    """LM Studio provider (OpenAI compatible)."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key or "lm-studio",
            base_url=config.base_url or "http://localhost:1234/v1"
        )
    
    async def generate_response(self, prompt: str) -> str:
        """Generate response using LM Studio (OpenAI compatible API)."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LM Studio API error: {str(e)}")


class AIProviderFactory:
    """Factory for creating AI providers."""
    
    @staticmethod
    def create_provider(config: AIProviderConfig) -> BaseAIProvider:
        """Create an AI provider based on the configuration."""
        if config.provider == AIProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == AIProvider.GEMINI:
            return GeminiProvider(config)
        elif config.provider == AIProvider.OLLAMA:
            return OllamaProvider(config)
        elif config.provider == AIProvider.LM_STUDIO:
            return LMStudioProvider(config)
        else:
            raise ValueError(f"Unsupported AI provider: {config.provider}")
