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
    
    def __init__(self):
        # Groq API configuration - load from environment variables only
        self.api_key = os.getenv('GROQ_API_KEY', '')
        self.default_model = os.getenv('AI_MODEL', 'llama-3.3-70b-versatile')
        
        # Validate API key
        if not self.api_key or self.api_key.startswith('your'):
            logger.warning("GROQ_API_KEY not configured - AI features will be disabled")
            
        # Initialize client
        self._client: Optional[Groq] = None
        
    @property
    def client(self) -> Groq:
        """Get or create Groq client"""
        if self._client is None:
            try:
                self._client = Groq(api_key=self.api_key)
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
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq chat completion failed: {e}")
            raise e

# Global instance
groq_config = GroqConfig()
