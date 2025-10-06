"""Application settings and environment variable management."""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Telegram Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.WEBHOOK_URL = os.getenv('WEBHOOK_URL')
        
        # Webhook Configuration
        self.WEBHOOK_HOST = '0.0.0.0'
        self.WEBHOOK_PORT = 10000
        
        # Delta Exchange Configuration
        self.DELTA_BASE_URL = 'https://api.india.delta.exchange'
        
        # Connection Pool Configuration
        self.POOL_CONNECTIONS = 10
        self.POOL_MAXSIZE = 20
        self.REQUEST_TIMEOUT = (3, 27)  # (connect, read) timeouts
        
        # Rate Limiting
        self.MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Cache Configuration
        self.PRODUCT_CACHE_TTL = 60  # seconds
        
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate required settings are present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL environment variable is required")

settings = Settings()
