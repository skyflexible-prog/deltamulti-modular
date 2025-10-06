"""User context management for maintaining conversation state."""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class UserContext:
    """Represents context for a single user session."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.account_index: Optional[int] = None
        self.account_credentials: Optional[Dict[str, str]] = None
        self.account_name: Optional[str] = None
        self.account_description: Optional[str] = None
        self.selected_asset: Optional[str] = None
        self.selected_expiry: Optional[int] = None
        self.selected_strike: Optional[float] = None
        self.call_product_id: Optional[int] = None
        self.put_product_id: Optional[int] = None
        self.lot_size: Optional[int] = None
        self.trade_direction: Optional[str] = None
        self.conversation_state: Optional[str] = None
        self.temp_data: Dict[str, Any] = {}
    
    def set_account(self, account_index: int, api_key: str, api_secret: str,
                   account_name: str = "", account_description: str = ""):
        """Set selected account credentials."""
        self.account_index = account_index
        self.account_credentials = {
            'api_key': api_key,
            'api_secret': api_secret
        }
        self.account_name = account_name
        self.account_description = account_description
        logger.info(f"User {self.user_id} selected account {account_index} ({account_name})")
        logger.debug(f"Credentials stored - API Key: {api_key[:10]}...")
    
    def has_account(self) -> bool:
        """Check if account is properly selected with valid credentials."""
        has_creds = (
            self.account_credentials is not None and
            isinstance(self.account_credentials, dict) and
            'api_key' in self.account_credentials and
            'api_secret' in self.account_credentials and
            self.account_credentials['api_key'] and
            self.account_credentials['api_secret']
        )
        
        if not has_creds:
            logger.warning(
                f"User {self.user_id} account check failed. "
                f"Credentials: {self.account_credentials}"
            )
        
        return has_creds
    
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
        self.account_name = None
        self.account_description = None
        self.clear_trade_data()
        self.conversation_state = None

class UserContextManager:
    """Manages context for all users using Singleton pattern."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure single instance across all imports."""
        if cls._instance is None:
            cls._instance = super(UserContextManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once."""
        if not UserContextManager._initialized:
            self.contexts: Dict[int, UserContext] = {}
            UserContextManager._initialized = True
            logger.info("UserContextManager initialized (Singleton)")
    
    def get_context(self, user_id: int) -> UserContext:
        """
        Get or create context for user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            UserContext instance
        """
        if user_id not in self.contexts:
            self.contexts[user_id] = UserContext(user_id)
            logger.debug(f"Created new context for user {user_id}")
        else:
            logger.debug(
                f"Retrieved existing context for user {user_id}. "
                f"Has account: {self.contexts[user_id].has_account()}"
            )
        
        return self.contexts[user_id]
    
    def clear_context(self, user_id: int):
        """
        Clear context for specific user.
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.contexts:
            self.contexts[user_id].clear_all()
            logger.debug(f"Cleared context for user {user_id}")
    
    def remove_context(self, user_id: int):
        """
        Remove context for specific user.
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.contexts:
            del self.contexts[user_id]
            logger.debug(f"Removed context for user {user_id}")
    
    def debug_context(self, user_id: int) -> str:
        """
        Get debug information about user context.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Debug string
        """
        if user_id not in self.contexts:
            return f"No context exists for user {user_id}"
        
        ctx = self.contexts[user_id]
        return (
            f"User {user_id} context:\n"
            f"  - Account Index: {ctx.account_index}\n"
            f"  - Account Name: {ctx.account_name}\n"
            f"  - Has Credentials: {ctx.has_account()}\n"
            f"  - Credentials: {ctx.account_credentials is not None}\n"
            f"  - Selected Asset: {ctx.selected_asset}\n"
            f"  - Conversation State: {ctx.conversation_state}"
        )
        
