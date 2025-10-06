"""Input validation functions."""
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def validate_lot_size(lot_input: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate lot size input.
    
    Args:
        lot_input: User input for lot size
    
    Returns:
        Tuple of (is_valid, lot_size, error_message)
    """
    try:
        lot_size = int(lot_input)
        
        if lot_size <= 0:
            return False, None, "Lot size must be positive"
        
        if lot_size > 1000:  # Reasonable upper limit
            return False, None, "Lot size too large (max: 1000)"
        
        return True, lot_size, None
    
    except ValueError:
        return False, None, "Invalid lot size. Please enter a number"

def validate_percentage(pct_input: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate percentage input.
    
    Args:
        pct_input: User input for percentage
    
    Returns:
        Tuple of (is_valid, percentage, error_message)
    """
    try:
        percentage = float(pct_input)
        
        if percentage <= 0:
            return False, None, "Percentage must be positive"
        
        if percentage > 100:
            return False, None, "Percentage too large (max: 100%)"
        
        return True, percentage, None
    
    except ValueError:
        return False, None, "Invalid percentage. Please enter a number"

def validate_price(price_input: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate price input.
    
    Args:
        price_input: User input for price
    
    Returns:
        Tuple of (is_valid, price, error_message)
    """
    try:
        price = float(price_input)
        
        if price <= 0:
            return False, None, "Price must be positive"
        
        if price > 1000000:  # Reasonable upper limit
            return False, None, "Price too large"
        
        return True, price, None
    
    except ValueError:
        return False, None, "Invalid price. Please enter a number"

def validate_account_index(index: int, max_accounts: int) -> bool:
    """
    Validate account index.
    
    Args:
        index: Account index to validate
        max_accounts: Maximum number of accounts
    
    Returns:
        True if valid, False otherwise
    """
    return 1 <= index <= max_accounts
  
