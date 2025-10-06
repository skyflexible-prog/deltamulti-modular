"""Account management and credentials handling."""
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Account:
    """Represents a Delta Exchange trading account."""
    
    def __init__(self, index: int, api_key: str, api_secret: str, 
                 name: str, description: str):
        self.index = index
        self.api_key = api_key
        self.api_secret = api_secret
        self.name = name
        self.description = description
    
    def __repr__(self):
        return f"Account(index={self.index}, name={self.name})"

class AccountManager:
    """Manages multiple Delta Exchange accounts from environment variables."""
    
    def __init__(self):
        self.accounts: Dict[int, Account] = {}
        self._load_accounts()
    
    def _load_accounts(self):
        """Load all configured accounts from environment variables."""
        for i in range(1, 6):  # Support up to 5 accounts
            api_key = os.getenv(f'ACCOUNT_{i}_API_KEY')
            api_secret = os.getenv(f'ACCOUNT_{i}_API_SECRET')
            name = os.getenv(f'ACCOUNT_{i}_NAME')
            description = os.getenv(f'ACCOUNT_{i}_DESCRIPTION')
            
            # Only add account if all required fields are present
            if api_key and api_secret and name:
                account = Account(
                    index=i,
                    api_key=api_key,
                    api_secret=api_secret,
                    name=name,
                    description=description or f"Trading Account {i}"
                )
                self.accounts[i] = account
                logger.info(f"Loaded account: {account.name} (index={i})")
        
        if not self.accounts:
            raise ValueError("No trading accounts configured. Please set at least ACCOUNT_1_* environment variables.")
        
        logger.info(f"Successfully loaded {len(self.accounts)} trading account(s)")
    
    def get_account(self, index: int) -> Optional[Account]:
        """Get account by index."""
        return self.accounts.get(index)
    
    def get_all_accounts(self) -> List[Account]:
        """Get all configured accounts."""
        return list(self.accounts.values())
    
    def get_account_count(self) -> int:
        """Get total number of configured accounts."""
        return len(self.accounts)
      
