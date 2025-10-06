"""Helper utility functions."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def calculate_atm_strike(spot_price: float, available_strikes: List[float]) -> float:
    """
    Calculate ATM (At-The-Money) strike based on spot price.
    
    Args:
        spot_price: Current spot price
        available_strikes: List of available strike prices
    
    Returns:
        Nearest strike price to spot
    """
    if not available_strikes:
        raise ValueError("No available strikes provided")
    
    atm_strike = min(available_strikes, key=lambda x: abs(x - spot_price))
    logger.debug(f"ATM strike for spot {spot_price}: {atm_strike}")
    return atm_strike

def calculate_stop_price_from_percentage(entry_price: float, percentage: float, 
                                        is_long: bool) -> float:
    """
    Calculate stop price based on percentage from entry.
    
    Args:
        entry_price: Entry price of position
        percentage: Stop loss percentage (positive value)
        is_long: True if long position, False if short
    
    Returns:
        Calculated stop price
    """
    if is_long:
        # For long: stop below entry
        stop_price = entry_price * (1 - percentage / 100)
    else:
        # For short: stop above entry
        stop_price = entry_price * (1 + percentage / 100)
    
    logger.debug(f"Stop price: {stop_price} (entry: {entry_price}, pct: {percentage}%, long: {is_long})")
    return stop_price

def calculate_target_price_from_percentage(entry_price: float, percentage: float,
                                          is_long: bool) -> float:
    """
    Calculate target price based on percentage from entry.
    
    Args:
        entry_price: Entry price of position
        percentage: Target percentage (positive value)
        is_long: True if long position, False if short
    
    Returns:
        Calculated target price
    """
    if is_long:
        # For long: target above entry
        target_price = entry_price * (1 + percentage / 100)
    else:
        # For short: target below entry
        target_price = entry_price * (1 - percentage / 100)
    
    logger.debug(f"Target price: {target_price} (entry: {entry_price}, pct: {percentage}%, long: {is_long})")
    return target_price

def determine_position_side(size: int) -> str:
    """
    Determine if position is long or short based on size.
    
    Args:
        size: Position size (positive for long, negative for short)
    
    Returns:
        "long" or "short"
    """
    return "long" if size > 0 else "short"

def get_opposite_side(side: str) -> str:
    """
    Get opposite order side.
    
    Args:
        side: "buy" or "sell"
    
    Returns:
        Opposite side
    """
    from config.constants import SIDE_BUY, SIDE_SELL
    return SIDE_SELL if side == SIDE_BUY else SIDE_BUY

def calculate_straddle_cost(call_price: float, put_price: float, lot_size: int) -> float:
    """
    Calculate total cost/credit for straddle.
    
    Args:
        call_price: Call option price
        put_price: Put option price
        lot_size: Number of lots
    
    Returns:
        Total cost (for long) or credit (for short)
    """
    return (call_price + put_price) * lot_size

def parse_callback_data(callback_data: str) -> Dict[str, str]:
    """
    Parse callback data string into dictionary.
    
    Args:
        callback_data: Colon-separated callback data (e.g., "select_account:1")
    
    Returns:
        Dictionary with parsed data
    """
    parts = callback_data.split(':')
    result = {'action': parts[0]}
    
    if len(parts) > 1:
        result['params'] = parts[1:]
    
    return result

def create_callback_data(action: str, *params) -> str:
    """
    Create callback data string.
    
    Args:
        action: Action identifier
        *params: Additional parameters
    
    Returns:
        Colon-separated callback data string
    """
    parts = [action] + [str(p) for p in params]
    return ':'.join(parts)

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunked lists
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
                            
