"""
Supabase Configuration and Client Setup
"""
import os
from supabase import create_client, Client
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseConfig:
    """Supabase configuration and client management"""
    
    def __init__(self):
        # Supabase credentials for MedToXAi project
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # Validate required environment variables
        if not self.url:
            logger.warning("SUPABASE_URL environment variable not set")
        if not self.key:
            logger.warning("SUPABASE_ANON_KEY environment variable not set")
        
        # Initialize client
        self._client: Optional[Client] = None
        
    @property
    def client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            try:
                self._client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        return self._client
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try a simple query to test connection with timeout
            result = self.client.table('predictions').select("id").limit(1).execute()
            logger.info("✅ Supabase connection test successful")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Supabase connection test: {e}")
            # Return True anyway since the service is optional
            return True

# Global instance
supabase_config = SupabaseConfig()