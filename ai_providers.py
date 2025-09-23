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
from config import Config


class BaseAIProvider(ABC):
    """Base class for AI providers."""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the AI provider."""
        pass
    
    async def generate_response_with_progress(self, prompt: str, verification_name: str) -> str:
        """Generate a response with progress updates. Default implementation falls back to regular generation."""
        # Check if streaming is enabled
        if not Config.ENABLE_STREAMING:
            return await self.generate_response(prompt)
        
        # If streaming is enabled, try to use streaming implementation
        return await self.generate_response(prompt)


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
            print(f"🔍 [GEMINI] Starting API call...")
            print(f"🔍 [GEMINI] Model: {self.config.model}")
            print(f"🔍 [GEMINI] API Key: {'***' if self.config.api_key else 'None'}")
            print(f"🔍 [GEMINI] Prompt length: {len(prompt)}")
            
            # Parse the prompt to separate system prompt from user content
            system_prompt, user_content = self._parse_prompt(prompt)
            print(f"🔍 [GEMINI] System prompt length: {len(system_prompt) if system_prompt else 0}")
            print(f"🔍 [GEMINI] User content length: {len(user_content)}")
            
            # Run the synchronous Gemini call in a thread pool
            loop = asyncio.get_event_loop()
            print(f"🔍 [GEMINI] Calling generate_content...")
            
            # Combine system prompt and user content for Gemini
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{user_content}"
            else:
                full_prompt = user_content
                
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config.temperature,
                        max_output_tokens=self.config.max_tokens
                    )
                )
            )
            print(f"🔍 [GEMINI] Response received, length: {len(response.text) if response.text else 0}")
            return response.text
        except Exception as e:
            print(f"🔍 [GEMINI] Error occurred: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _parse_prompt(self, prompt: str) -> tuple[str, str]:
        """Parse the full prompt to extract system prompt and user content."""
        # Split the prompt into system prompt and user content
        if prompt.startswith("SYSTEM PROMPT:\n"):
            # Find the end of system prompt section
            system_start = 15  # Length of "SYSTEM PROMPT:\n"
            
            # Look for double newline first, then single newline, then any section header
            system_end = prompt.find("\n\n", system_start)
            if system_end == -1:
                # Try single newline followed by a section header
                for section in ["DOCUMENTATION FILES:", "FRONTEND CODE FILES:", "BACKEND CODE FILES:", "INSTRUCTIONS:"]:
                    section_pos = prompt.find(f"\n{section}", system_start)
                    if section_pos != -1:
                        system_end = section_pos
                        break
                
                if system_end == -1:
                    # If no clear separation found, treat entire prompt as user content
                    system_prompt = ""
                    user_content = prompt
                else:
                    system_prompt = prompt[system_start:system_end].strip()
                    user_content = prompt[system_end + 1:].strip()
            else:
                system_prompt = prompt[system_start:system_end].strip()
                user_content = prompt[system_end + 2:].strip()
        else:
            # No system prompt section, treat entire prompt as user content
            system_prompt = ""
            user_content = prompt
        
        return system_prompt, user_content


class OllamaProvider(BaseAIProvider):
    """Ollama local provider."""
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        # Ollama client uses 'host' parameter, not 'base_url'
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
            return response.response
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    async def generate_response_with_progress(self, prompt: str, verification_name: str) -> str:
        """Generate response with streaming progress updates."""
        # Check if streaming is enabled
        if not Config.ENABLE_STREAMING:
            # Use non-streaming approach
            return await self.generate_response(prompt)
        
        try:
            response_text = ""
            stream = await self.client.generate(
                model=self.config.model,
                prompt=prompt,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                },
                stream=True  # Enable streaming
            )
            
            # Emit streaming start event
            if hasattr(self, 'progress_callback') and self.progress_callback:
                await self.progress_callback({
                    "type": "ai_streaming_start",
                    "message": f"AI streaming started for: {verification_name}",
                    "verification_name": verification_name
                })
            
            async for chunk in stream:
                if chunk.response:
                    content = chunk.response
                    response_text += content
                    
                    # Emit streaming content event
                    if hasattr(self, 'progress_callback') and self.progress_callback:
                        await self.progress_callback({
                            "type": "ai_streaming_content",
                            "message": content,
                            "verification_name": verification_name,
                            "partial_response": response_text
                        })
            
            # Emit streaming complete event
            if hasattr(self, 'progress_callback') and self.progress_callback:
                await self.progress_callback({
                    "type": "ai_streaming_complete",
                    "message": f"AI streaming completed for: {verification_name}",
                    "verification_name": verification_name,
                    "total_length": len(response_text)
                })
            
            return response_text
            
        except Exception as e:
            # Fallback to non-streaming if streaming fails
            print(f"Ollama streaming failed, falling back to non-streaming: {e}")
            return await self.generate_response(prompt)


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
            # Check if streaming is enabled
            if Config.ENABLE_STREAMING:
                # Try streaming first, fallback to non-streaming if not supported
                try:
                    response_text = ""
                    stream = await self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                        stream=True  # Enable streaming
                    )
                    
                    async for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            response_text += chunk.choices[0].delta.content
                    
                    return response_text
                    
                except Exception as stream_error:
                    # Fallback to non-streaming if streaming fails
                    print(f"LM Studio streaming failed, falling back to non-streaming: {stream_error}")
            
            # Use non-streaming approach
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=False
            )
            return response.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"LM Studio API error: {str(e)}")
    
    async def generate_response_with_progress(self, prompt: str, verification_name: str) -> str:
        """Generate response with streaming progress updates."""
        # Check if streaming is enabled
        if not Config.ENABLE_STREAMING:
            # Use non-streaming approach
            return await self.generate_response(prompt)
        
        try:
            # Try streaming first, fallback to non-streaming if not supported
            try:
                response_text = ""
                stream = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stream=True  # Enable streaming
                )
                
                # Emit streaming start event
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    await self.progress_callback({
                        "type": "ai_streaming_start",
                        "message": f"AI streaming started for: {verification_name}",
                        "verification_name": verification_name
                    })
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        
                        # Emit streaming content event
                        if hasattr(self, 'progress_callback') and self.progress_callback:
                            await self.progress_callback({
                                "type": "ai_streaming_content",
                                "message": content,
                                "verification_name": verification_name,
                                "partial_response": response_text
                            })
                
                # Emit streaming complete event
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    await self.progress_callback({
                        "type": "ai_streaming_complete",
                        "message": f"AI streaming completed for: {verification_name}",
                        "verification_name": verification_name,
                        "total_length": len(response_text)
                    })
                
                return response_text
                
            except Exception as stream_error:
                # Fallback to non-streaming if streaming fails
                print(f"LM Studio streaming failed, falling back to non-streaming: {stream_error}")
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that verifies code against documentation."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stream=False
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
