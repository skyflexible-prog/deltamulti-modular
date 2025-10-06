"""Trade execution callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from config.constants import (
    CALLBACK_SELECT_LOT, CALLBACK_CUSTOM_LOT, CALLBACK_TRADE_DIRECTION,
    CALLBACK_CONFIRM_TRADE, CALLBACK_CANCEL_TRADE, CALLBACK_MAIN_MENU,
    DIRECTION_LONG, DIRECTION_SHORT, STATE_AWAITING_CUSTOM_LOT,
    EMOJI_ROCKET, EMOJI_CHECK, EMOJI_CROSS, SIDE_BUY, SIDE_SELL
)
from delta_api.client import DeltaClient
from delta_api.orders import OrderAPI
from delta_api.products import ProductAPI
from utils.helpers import (
    create_callback_data, parse_callback_data, calculate_straddle_cost
)
from utils.validators import validate_lot_size
from utils.formatters import format_price, format_straddle_details
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

context_manager = UserContextManager()

async def handle_lot_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle predefined lot size selection.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    callback_data = parse_callback_data(query.data)
    
    try:
        # Extract lot size from callback
        lot_size = int(callback_data['params'][0])
        user_context.lot_size = lot_size
        
        logger.info(f"User {user_id} selected lot size: {lot_size}")
        
        # Display trade direction selection
        await _show_trade_direction_selection(query, user_context)
    
    except Exception as e:
        logger.error(f"Error in lot selection: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try again.",
            parse_mode='HTML'
        )

async def handle_custom_lot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle custom lot callback - prompt user to enter lot size.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    # Set conversation state
    user_context.conversation_state = STATE_AWAITING_CUSTOM_LOT
    
    # Build cancel keyboard
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data=CALLBACK_MAIN_MENU)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✏️ <b>Enter Custom Lot Size:</b>\n\n"
        "Please type the number of lots you want to trade.\n"
        "<i>Example: 3</i>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_custom_lot_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle custom lot size input from user.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    # Check if waiting for custom lot input
    if user_context.conversation_state != STATE_AWAITING_CUSTOM_LOT:
        return
    
    user_input = update.message.text.strip()
    
    # Validate lot size
    is_valid, lot_size, error_msg = validate_lot_size(user_input)
    
    if not is_valid:
        await update.message.reply_text(
            f"❌ {error_msg}\n\nPlease enter a valid lot size:",
            parse_mode='HTML'
        )
        return
    
    # Store lot size
    user_context.lot_size = lot_size
    user_context.conversation_state = None
    
    logger.info(f"User {user_id} entered custom lot size: {lot_size}")
    
    # Display trade direction selection
    await _show_trade_direction_selection_message(update, user_context)

async def handle_trade_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle trade direction selection (long or short straddle).
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    callback_data = parse_callback_data(query.data)
    
    try:
        # Extract direction from callback
        direction = callback_data['params'][0]
        user_context.trade_direction = direction
        
        logger.info(f"User {user_id} selected trade direction: {direction}")
        
        # Show confirmation with trade details
        await _show_trade_confirmation(query, user_context)
    
    except Exception as e:
        logger.error(f"Error in trade direction selection: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try again.",
            parse_mode='HTML'
        )

async def handle_trade_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle trade confirmation - execute the straddle order.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    callback_data = parse_callback_data(query.data)
    
    try:
        action = callback_data['action']
        
        if action == CALLBACK_CANCEL_TRADE:
            # User cancelled the trade
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ Trade cancelled.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Clear trade data
            user_context.clear_trade_data()
            return
        
        # Confirm execution
        if action != CALLBACK_CONFIRM_TRADE:
            return
        
        # Validate all required data is present
        if not all([
            user_context.call_product_id,
            user_context.put_product_id,
            user_context.lot_size,
            user_context.trade_direction
        ]):
            await query.edit_message_text(
                "❌ Missing trade data. Please start over.",
                parse_mode='HTML'
            )
            return
        
        # Show executing message
        await query.edit_message_text(
            f"{EMOJI_ROCKET} <b>Executing Trade...</b>\n\n"
            "Please wait while we place your orders.",
            parse_mode='HTML'
        )
        
        # Determine order side based on direction
        side = SIDE_BUY if user_context.trade_direction == DIRECTION_LONG else SIDE_SELL
        
        # Execute straddle orders
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            order_api = OrderAPI(client)
            
            result = order_api.place_straddle_orders(
                call_product_id=user_context.call_product_id,
                put_product_id=user_context.put_product_id,
                side=side,
                size=user_context.lot_size
            )
        
        # Format execution results
        call_order = result['call_order']
        put_order = result['put_order']
        
        direction_text = "LONG" if user_context.trade_direction == DIRECTION_LONG else "SHORT"
        
        execution_text = (
            f"{EMOJI_CHECK} <b>Trade Executed Successfully!</b>\n\n"
            f"<b>Strategy:</b> {direction_text} Straddle\n"
            f"<b>Lot Size:</b> {user_context.lot_size}\n\n"
            f"<b>Call Order:</b>\n"
            f"Order ID: {call_order.get('id')}\n"
            f"Product ID: {call_order.get('product_id')}\n"
            f"Size: {call_order.get('size')}\n"
            f"Side: {call_order.get('side').upper()}\n\n"
            f"<b>Put Order:</b>\n"
            f"Order ID: {put_order.get('id')}\n"
            f"Product ID: {put_order.get('product_id')}\n"
            f"Size: {put_order.get('size')}\n"
            f"Side: {put_order.get('side').upper()}\n\n"
            f"✅ Both legs executed at market price."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            execution_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Clear trade data
        user_context.clear_trade_data()
        
        logger.info(f"User {user_id} successfully executed {direction_text} straddle")
    
    except Exception as e:
        logger.error(f"Error executing trade: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_CROSS} <b>Trade Execution Failed</b>\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check your account balance and try again.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Clear trade data
        user_context.clear_trade_data()

async def _show_trade_direction_selection(query, user_context):
    """
    Show trade direction selection keyboard.
    
    Args:
        query: Callback query object
        user_context: User context
    """
    keyboard = [
        [InlineKeyboardButton(
            "📈 Long Straddle (Buy)",
            callback_data=create_callback_data(CALLBACK_TRADE_DIRECTION, DIRECTION_LONG)
        )],
        [InlineKeyboardButton(
            "📉 Short Straddle (Sell)",
            callback_data=create_callback_data(CALLBACK_TRADE_DIRECTION, DIRECTION_SHORT)
        )],
        [InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_MAIN_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{EMOJI_ROCKET} <b>Select Trade Direction:</b>\n\n"
        f"<b>Lot Size:</b> {user_context.lot_size}\n\n"
        f"<b>Long Straddle:</b> Buy both Call and Put (profit from large moves)\n"
        f"<b>Short Straddle:</b> Sell both Call and Put (profit from low volatility)",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def _show_trade_direction_selection_message(update, user_context):
    """
    Show trade direction selection in new message.
    
    Args:
        update: Update object
        user_context: User context
    """
    keyboard = [
        [InlineKeyboardButton(
            "📈 Long Straddle (Buy)",
            callback_data=create_callback_data(CALLBACK_TRADE_DIRECTION, DIRECTION_LONG)
        )],
        [InlineKeyboardButton(
            "📉 Short Straddle (Sell)",
            callback_data=create_callback_data(CALLBACK_TRADE_DIRECTION, DIRECTION_SHORT)
        )],
        [InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_MAIN_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{EMOJI_ROCKET} <b>Select Trade Direction:</b>\n\n"
        f"<b>Lot Size:</b> {user_context.lot_size}\n\n"
        f"<b>Long Straddle:</b> Buy both Call and Put (profit from large moves)\n"
        f"<b>Short Straddle:</b> Sell both Call and Put (profit from low volatility)",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def _show_trade_confirmation(query, user_context):
    """
    Show trade confirmation with full details.
    
    Args:
        query: Callback query object
        user_context: User context
    """
    try:
        # Fetch current prices for display
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            product_api = ProductAPI(client)
            
            call_prices = product_api.get_option_prices(user_context.call_product_id)
            put_prices = product_api.get_option_prices(user_context.put_product_id)
        
        # Calculate estimated cost
        call_cost = call_prices['mark_price'] * user_context.lot_size
        put_cost = put_prices['mark_price'] * user_context.lot_size
        total_cost = call_cost + put_cost
        
        direction_text = "LONG" if user_context.trade_direction == DIRECTION_LONG else "SHORT"
        action_text = "BUY" if user_context.trade_direction == DIRECTION_LONG else "SELL"
        
        expiry_dt = datetime.fromtimestamp(user_context.selected_expiry)
        
        confirmation_text = (
            f"{EMOJI_ROCKET} <b>Confirm Trade Execution</b>\n\n"
            f"<b>Strategy:</b> {direction_text} Straddle\n"
            f"<b>Asset:</b> {user_context.selected_asset}\n"
            f"<b>Expiry:</b> {expiry_dt.strftime('%d %b %Y %H:%M')}\n"
            f"<b>Strike:</b> {format_price(user_context.selected_strike)}\n"
            f"<b>Lot Size:</b> {user_context.lot_size}\n\n"
            f"<b>Call Option:</b>\n"
            f"Mark Price: {format_price(call_prices['mark_price'])}\n"
            f"Est. Cost: {format_price(call_cost)}\n\n"
            f"<b>Put Option:</b>\n"
            f"Mark Price: {format_price(put_prices['mark_price'])}\n"
            f"Est. Cost: {format_price(put_cost)}\n\n"
            f"<b>Total Est. {'Cost' if direction_text == 'LONG' else 'Credit'}:</b> "
            f"{format_price(total_cost)}\n\n"
            f"⚠️ This will {action_text} both options at market price.\n"
            f"Are you sure you want to proceed?"
        )
        
        keyboard = [
            [InlineKeyboardButton(
                f"{EMOJI_CHECK} Confirm Execution",
                callback_data=CALLBACK_CONFIRM_TRADE
            )],
            [InlineKeyboardButton(
                f"{EMOJI_CROSS} Cancel Trade",
                callback_data=CALLBACK_CANCEL_TRADE
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error showing trade confirmation: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Failed to load trade confirmation.\nError: {str(e)}",
            parse_mode='HTML'
        )
          
