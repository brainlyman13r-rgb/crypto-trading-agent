"""LLM Adapter - Abstraction for OpenAI, Anthropic, or local LLM."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseLLMAdapter:
    """Base class for LLM adapters."""
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate LLM response."""
        raise NotImplementedError


class OpenAILLMAdapter(BaseLLMAdapter):
    """OpenAI GPT adapter."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model = model
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.error("OpenAI library not installed")
            self.client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate response using OpenAI GPT."""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None


class AnthropicLLMAdapter(BaseLLMAdapter):
    """Anthropic Claude adapter."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.error("Anthropic library not installed")
            self.client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate response using Claude."""
        if not self.client:
            return None
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
