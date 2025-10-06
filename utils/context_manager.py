"""User context management for maintaining conversation state."""
import logging
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class UserContext:
    """Represents context for a single user session."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.account_index: Optional[int] = None
        self.account_credentials: Optional[Dict[str, str]] = None
        self.selected_asset: Optional[str] = None
        self.selected_expiry: Optional[int] = None
        self.selected_strike: Optional[float] = None
        self.call_product_id: Optional[int] = None
        self.put_product_id: Optional[int] = None
        self.lot_size: Optional[int] = None
        self.trade_direction: Optional[str] = None
        self.conversation_state: Optional[str] = None
        self.temp_data: Dict[str, Any] = {}
    
    def set_account(self, account_index: int, api_key: str, api_secret: str):
        """Set selected account credentials."""
        self.account_index = account_index
        self.account_credentials = {
            'api_key': api_key,
            'api_secret': api_secret
        }
        logger.info(f"User {self.user_id} selected account {account_index}")
    
    def clear_trade_data(self):
        """Clear trade-specific data."""
        self.selected_asset = None
        self.selected_expiry = None
        self.selected_strike = None
        self.call_product_id = None
        self.put_product_id = None
        self.lot_size = None
        self.trade_direction = None
        self.temp_data = {}
    
    def clear_all(self):
        """Clear all context data."""
        self.account_index = None
        self.account_credentials = None
        self.clear_trade_data()
        self.conversation_state = None

class UserContextManager:
    """Manages context for all users."""
    
    def __init__(self):
        self.contexts: Dict[int, UserContext] = {}
        self.lock = Lock()
    
    def get_context(self, user_id: int) -> UserContext:
        """
        Get or create context for user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            UserContext instance
        """
        with self.lock:
            if user_id not in self.contexts:
                self.contexts[user_id] = UserContext(user_id)
                logger.debug(f"Created new context for user {user_id}")
            return self.contexts[user_id]
    
    def clear_context(self, user_id: int):
        """
        Clear context for specific user.
        
        Args:
            user_id: Telegram user ID
        """
        with self.lock:
            if user_id in self.contexts:
                self.contexts[user_id].clear_all()
                logger.debug(f"Cleared context for user {user_id}")
    
    def remove_context(self, user_id: int):
        """
        Remove context for specific user.
        
        Args:
            user_id: Telegram user ID
        """
        with self.lock:
            if user_id in self.contexts:
                del self.contexts[user_id]
                logger.debug(f"Removed context for user {user_id}")
      
