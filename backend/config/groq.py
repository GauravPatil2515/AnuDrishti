"""
Groq AI Configuration and Client Setup
"""
import os
from groq import Groq
from typing import Optional, Dict, Any, List
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqConfig:
    """Groq AI configuration and client management"""
    
    # Hard timeout (seconds) for any single LLM call. Prevents the whole
    # request thread from hanging on a slow/free-tier Groq response (SIH audit
    # Bug #3: "No Error Boundary on LLM Timeout").
    REQUEST_TIMEOUT = 30

    def __init__(self):
        # Groq API configuration - load from environment variables only
        self.api_key = os.getenv('GROQ_API_KEY', '')
        self.default_model = os.getenv('AI_MODEL', 'llama-3.3-70b-versatile')
        
        # Validate API key
        if not self.api_key or self.api_key.startswith('your'):
            logger.warning("GROQ_API_KEY not configured - AI features will be disabled")
            self._client = None
            return
            
        # Initialize client
        self._client: Optional[Groq] = None
        
    @property
    def client(self) -> Groq:
        """Get or create Groq client"""
        if self._client is None:
            if not self.api_key or self.api_key.startswith('your'):
                raise RuntimeError("GROQ_API_KEY not configured - AI features disabled")
            try:
                self._client = Groq(
                    api_key=self.api_key,
                    timeout=self.REQUEST_TIMEOUT
                )
                logger.info("✅ Groq client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq client: {e}")
                raise e
        return self._client

    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 1024) -> str:
        """Generate chat completion using Groq AI"""
        try:
            if self._client is None:
                self.client
            
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.REQUEST_TIMEOUT
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq chat completion failed: {e}")
            raise e

    def generate(self,
                 prompt: str,
                 max_tokens: int = 800,
                 temperature: float = 0.2) -> Optional[str]:
        """Single-prompt completion used by the ConstrainedExplainer.

        Returns the model text, or ``None`` on any failure (timeout, auth,
        network) so callers can fall back to a rule-based explanation instead
        of hanging the request. Wrapped in its own timeout guard.
        """
        if not self.api_key or self.api_key.startswith('your'):
            logger.warning("Groq generate() called without a configured API key")
            return None
        messages = [
            {
                "role": "system",
                "content": ("You are a precise computational toxicology explanation engine. "
                            "You output only valid, parseable JSON that matches the requested schema.")
            },
            {"role": "user", "content": prompt}
        ]
        try:
            return self.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"Groq generate() failed (fallback will be used): {e}")
            return None

# Global instance (lazy initialization)
_groq_config = None

def get_groq_config():
    """Get or create the global GroqConfig instance"""
    global _groq_config
    if _groq_config is None:
        _groq_config = GroqConfig()
    return _groq_config

# For backward compatibility - create a proxy object
class _GroqConfigProxy:
    def __getattr__(self, name):
        return getattr(get_groq_config(), name)

groq_config = _GroqConfigProxy()
