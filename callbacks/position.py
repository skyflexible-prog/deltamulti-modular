"""Position-related callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.constants import CALLBACK_MAIN_MENU, EMOJI_CHART
from delta_api.client import DeltaClient
from delta_api.positions import PositionAPI
from delta_api.products import ProductAPI  # ADD THIS LINE
from utils.formatters import format_position, format_pnl  # ADD format_pnl HERE
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

context_manager = UserContextManager()

async def handle_show_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle show positions callback - display all open positions.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    if not user_context.has_account():
        await query.edit_message_text(
            "❌ No account selected. Please use /start to select an account.",
            parse_mode='HTML'
        )
        return
    
    # Show loading message
    await query.edit_message_text(
        "⏳ Fetching open positions...",
        parse_mode='HTML'
    )
    
    try:
        # Fetch positions
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            position_api = PositionAPI(client)
            product_api = ProductAPI(client)  # ADD THIS LINE
            
            positions = position_api.get_positions()
            
            # ADD THESE LINES (lines 54-67):
            if positions:
                # Fetch all tickers to get mark prices
                all_tickers = product_api.get_tickers()
                # all_tickers is {'result': [...list of tickers...]}
                tickers_list = all_tickers if isinstance(all_tickers, list) else all_tickers.get('result', [])
                ticker_map = {t['symbol']: t for t in tickers_list}

                
                # Enrich positions with mark_price
                for position in positions:
                    product = position.get('product', {})
                    symbol = product.get('symbol', 'Unknown')
                    ticker = ticker_map.get(symbol, {})
                    
                    # Add mark_price from ticker
                    position['mark_price'] = float(ticker.get('mark_price', 0))
        
        if not positions:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{EMOJI_CHART} <b>Open Positions</b>\n\n"
                "You have no active positions.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Format positions
        positions_text = f"{EMOJI_CHART} <b>Open Positions</b>\n\n"
        
        for i, position in enumerate(positions, 1):
            positions_text += f"<b>Position {i}:</b>\n"
            positions_text += format_position(position)
            positions_text += "\n\n"
        
        # Add summary
        total_pnl = sum(float(p.get('unrealized_profit_loss', 0)) for p in positions)
        positions_text += f"<b>Total Unrealized PnL:</b> {format_pnl(total_pnl)}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            positions_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error fetching positions: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch positions.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
