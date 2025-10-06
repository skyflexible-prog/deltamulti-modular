"""Formatting functions for display."""
import logging
from typing import Dict, Any
from datetime import datetime

from config.constants import EMOJI_MONEY, EMOJI_CHART, EMOJI_WARNING

logger = logging.getLogger(__name__)

def format_price(price: float, decimals: int = 2) -> str:
    """
    Format price for display.
    
    Args:
        price: Price value
        decimals: Number of decimal places
    
    Returns:
        Formatted price string
    """
    # Convert to float if it's a string
    if isinstance(price, str):
        try:
            price = float(price)
        except (ValueError, TypeError):
            return "0.00"
    
    # Handle None or invalid values
    if price is None:
        return "0.00"
    
    return f"{price:,.{decimals}f}"

def format_percentage(percentage: float, decimals: int = 2) -> str:
    """
    Format percentage for display.
    
    Args:
        percentage: Percentage value
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    # Convert to float if it's a string
    if isinstance(percentage, str):
        try:
            percentage = float(percentage)
        except (ValueError, TypeError):
            return "0.00%"
    
    # Handle None or invalid values
    if percentage is None:
        return "0.00%"
    
    return f"{percentage:.{decimals}f}%"

def format_pnl(pnl: float) -> str:
    """
    Format PnL with color indicators.
    
    Args:
        pnl: PnL value
    
    Returns:
        Formatted PnL string with emoji
    """
    # Convert to float if it's a string
    if isinstance(pnl, str):
        try:
            pnl = float(pnl)
        except (ValueError, TypeError):
            return "0.00"
    
    # Handle None
    if pnl is None:
        return "0.00"
    
    if pnl > 0:
        return f"✅ +{format_price(pnl)}"
    elif pnl < 0:
        return f"❌ {format_price(pnl)}"
    else:
        return f"{format_price(pnl)}"

def format_datetime(timestamp: int) -> str:
    """
    Format Unix timestamp to readable datetime.
    
    Args:
        timestamp: Unix timestamp in seconds
    
    Returns:
        Formatted datetime string
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%d %b %Y %H:%M")

def format_position(position: Dict[str, Any]) -> str:
    """
    Format position data for display.
    
    Args:
        position: Position dictionary
    
    Returns:
        Formatted position string
    """
    symbol = position.get('symbol', 'Unknown')
    size = position.get('size', 0)
    entry_price = position.get('entry_price', 0)
    mark_price = position.get('mark_price', 0)
    pnl = position.get('unrealized_profit_loss', 0)
    
    side = "LONG" if size > 0 else "SHORT"
    
    text = f"{EMOJI_CHART} <b>{symbol}</b>\n"
    text += f"Side: {side} | Size: {abs(size)}\n"
    text += f"Entry: {format_price(entry_price)} | Mark: {format_price(mark_price)}\n"
    text += f"PnL: {format_pnl(pnl)}"
    
    return text

def format_order(order: Dict[str, Any]) -> str:
    """
    Format order data for display.
    
    Args:
        order: Order dictionary
    
    Returns:
        Formatted order string
    """
    symbol = order.get('symbol', 'Unknown')
    side = order.get('side', '').upper()
    size = order.get('size', 0)
    order_type = order.get('order_type', 'unknown')
    stop_type = order.get('stop_order_type', '')
    
    text = f"<b>{symbol}</b>\n"
    text += f"{side} {size} | Type: {order_type}\n"
    
    if stop_type:
        text += f"Stop Type: {stop_type}\n"
        stop_price = order.get('stop_price')
        if stop_price:
            text += f"Trigger: {format_price(stop_price)}\n"
    
    limit_price = order.get('limit_price')
    if limit_price:
        text += f"Limit: {format_price(limit_price)}"
    
    return text

def format_account_summary(summary: Dict[str, Any], account_name: str, 
                          account_desc: str) -> str:
    """
    Format account summary for display.
    
    Args:
        summary: Account summary dictionary
        account_name: Account name
        account_desc: Account description
    
    Returns:
        Formatted account summary string
    """
    text = f"{EMOJI_MONEY} <b>{account_name}</b>\n"
    text += f"<i>{account_desc}</i>\n\n"
    text += f"<b>Account Balance:</b>\n"
    text += f"Available: {format_price(summary.get('available_balance', 0))}\n"
    text += f"Margin Used: {format_price(summary.get('margin_used', 0))}\n"
    text += f"Total Equity: {format_price(summary.get('total_equity', 0))}\n"
    text += f"Unrealized PnL: {format_pnl(summary.get('unrealized_pnl', 0))}"
    
    return text

def format_straddle_details(asset: str, expiry_dt: datetime, spot_price: float,
                           strike: float, call_data: Dict, put_data: Dict) -> str:
    """
    Format ATM straddle details for display.
    
    Args:
        asset: Underlying asset symbol (BTCUSD or ETHUSD)
        expiry_dt: Expiry datetime
        spot_price: Current spot price
        strike: ATM strike price
        call_data: Call option data dict with keys: product_id, symbol, strike, mark_price, bid, ask
        put_data: Put option data dict with keys: product_id, symbol, strike, mark_price, bid, ask
    
    Returns:
        Formatted straddle details string
    """
    # Get prices - use correct dictionary keys
    call_mark = call_data.get('mark_price', 0)
    put_mark = put_data.get('mark_price', 0)
    call_bid = call_data.get('bid', 0)
    call_ask = call_data.get('ask', 0)
    put_bid = put_data.get('bid', 0)
    put_ask = put_data.get('ask', 0)
    
    total_cost = call_mark + put_mark
    
    text = f"{EMOJI_CHART} <b>ATM Straddle Details</b>\n\n"
    text += f"<b>Underlying:</b> {asset}\n"
    text += f"<b>Expiry:</b> {expiry_dt.strftime('%d %b %Y %H:%M')}\n"
    text += f"<b>Spot Price:</b> {format_price(spot_price)}\n"
    text += f"<b>ATM Strike:</b> {format_price(strike)}\n\n"
    
    text += f"📞 <b>Call Option (CE):</b>\n"
    text += f"Symbol: {call_data.get('symbol', 'N/A')}\n"
    text += f"Mark: {format_price(call_mark)}\n"
    text += f"Bid: {format_price(call_bid)} | Ask: {format_price(call_ask)}\n\n"
    
    text += f"📝 <b>Put Option (PE):</b>\n"
    text += f"Symbol: {put_data.get('symbol', 'N/A')}\n"
    text += f"Mark: {format_price(put_mark)}\n"
    text += f"Bid: {format_price(put_bid)} | Ask: {format_price(put_ask)}\n\n"
    
    text += f"<b>Cost per Lot:</b>\n"
    text += f"CE: {format_price(call_mark)} | PE: {format_price(put_mark)}\n"
    text += f"<b>Total: {format_price(total_cost)}</b>"
    
    return text
                               
