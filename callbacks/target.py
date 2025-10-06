"""Target (take-profit) related callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.constants import (
    CALLBACK_SET_TARGET, CALLBACK_TARGET_POSITION, CALLBACK_TARGET_METHOD,
    CALLBACK_CONFIRM_TARGET, CALLBACK_MAIN_MENU,
    STATE_AWAITING_TARGET_TRIGGER_PCT, STATE_AWAITING_TARGET_LIMIT_PCT,
    STATE_AWAITING_TARGET_TRIGGER_NUM, STATE_AWAITING_TARGET_LIMIT_NUM,
    EMOJI_TARGET, EMOJI_CHECK, EMOJI_CROSS, SIDE_BUY, SIDE_SELL, CALLBACK_CUSTOM_LOT
)
from delta_api.client import DeltaClient
from delta_api.positions import PositionAPI
from delta_api.orders import OrderAPI
from utils.helpers import (
    create_callback_data, parse_callback_data,
    calculate_target_price_from_percentage
)
from utils.validators import validate_percentage, validate_price
from utils.formatters import format_price, format_percentage
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

context_manager = UserContextManager()

async def handle_set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle set target callback - display positions for selection.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    if not user_context.account_credentials:
        await query.edit_message_text(
            "❌ No account selected. Please use /start to select an account.",
            parse_mode='HTML'
        )
        return
    
    # Clear previous data
    user_context.conversation_state = None
    user_context.temp_data = {}
    
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
            positions = position_api.get_positions()
        
        if not positions:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{EMOJI_TARGET} <b>Set Target</b>\n\n"
                "You have no active positions.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Build position selection keyboard
        keyboard = []
        for position in positions:
            button_text = f"{position['symbol']} | Size: {abs(position['size'])}"
            callback_data = create_callback_data(
                CALLBACK_TARGET_POSITION,
                position['product_id'],
                position['size'],
                position['entry_price']
            )
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_TARGET} <b>Set Target</b>\n\n"
            f"Select a position to set target:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error fetching positions for target: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch positions.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_target_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle position selection for target - show method selection.
    
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
        # Extract position data
        product_id = int(callback_data['params'][0])
        size = int(callback_data['params'][1])
        entry_price = float(callback_data['params'][2])
        
        # Store in temp data
        user_context.temp_data['target_product_id'] = product_id
        user_context.temp_data['target_size'] = size
        user_context.temp_data['target_entry_price'] = entry_price
        
        position_side = "LONG" if size > 0 else "SHORT"
        
        # Build method selection keyboard
        keyboard = [
            [InlineKeyboardButton(
                "📊 Percentage",
                callback_data=create_callback_data(CALLBACK_TARGET_METHOD, "percentage")
            )],
            [InlineKeyboardButton(
                "🔢 Numeral",
                callback_data=create_callback_data(CALLBACK_TARGET_METHOD, "numeral")
            )],
            [InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_SET_TARGET)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_TARGET} <b>Set Target</b>\n\n"
            f"<b>Position:</b> {position_side}\n"
            f"<b>Size:</b> {abs(size)}\n"
            f"<b>Entry Price:</b> {format_price(entry_price)}\n\n"
            f"Select input method:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error in target position selection: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try again.",
            parse_mode='HTML'
        )

async def handle_target_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle method selection for target - prompt for input.
    
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
        method = callback_data['params'][0]
        user_context.temp_data['target_method'] = method
        
        if method == "percentage":
            user_context.conversation_state = STATE_AWAITING_TARGET_TRIGGER_PCT
            prompt_text = (
                f"{EMOJI_TARGET} <b>Target - Trigger Percentage</b>\n\n"
                "Enter the trigger price percentage from entry price.\n"
                "<i>Example: 10 (for 10% above entry for long, below for short)</i>"
            )
        else:  # numeral
            user_context.conversation_state = STATE_AWAITING_TARGET_TRIGGER_NUM
            prompt_text = (
                f"{EMOJI_TARGET} <b>Target - Trigger Price</b>\n\n"
                "Enter the trigger price as a numerical value.\n"
                "<i>Example: 105000</i>"
            )
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            prompt_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error in target method selection: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try again.",
            parse_mode='HTML'
        )

async def handle_target_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle target input from user (trigger and limit prices).
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    state = user_context.conversation_state
    
    # Check if we're in a target input state
    if state not in [
        STATE_AWAITING_TARGET_TRIGGER_PCT, STATE_AWAITING_TARGET_LIMIT_PCT,
        STATE_AWAITING_TARGET_TRIGGER_NUM, STATE_AWAITING_TARGET_LIMIT_NUM
    ]:
        return
    
    user_input = update.message.text.strip()
    
    try:
        # Validate based on state
        if state in [STATE_AWAITING_TARGET_TRIGGER_PCT, STATE_AWAITING_TARGET_LIMIT_PCT]:
            is_valid, value, error_msg = validate_percentage(user_input)
        else:
            is_valid, value, error_msg = validate_price(user_input)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {error_msg}\n\nPlease try again:",
                parse_mode='HTML'
            )
            return
        
        # Store value and move to next state
        if state == STATE_AWAITING_TARGET_TRIGGER_PCT:
            user_context.temp_data['target_trigger_pct'] = value
            user_context.conversation_state = STATE_AWAITING_TARGET_LIMIT_PCT
            
            await update.message.reply_text(
                f"{EMOJI_TARGET} <b>Target - Limit Percentage</b>\n\n"
                "Enter the limit price percentage from entry price.\n"
                "<i>Example: 9.5</i>",
                parse_mode='HTML'
            )
        
        elif state == STATE_AWAITING_TARGET_LIMIT_PCT:
            user_context.temp_data['target_limit_pct'] = value
            user_context.conversation_state = None
            
            # Show confirmation
            await _show_target_confirmation(update, user_context)
        
        elif state == STATE_AWAITING_TARGET_TRIGGER_NUM:
            user_context.temp_data['target_trigger_price'] = value
            user_context.conversation_state = STATE_AWAITING_TARGET_LIMIT_NUM
            
            await update.message.reply_text(
                f"{EMOJI_TARGET} <b>Target - Limit Price</b>\n\n"
                "Enter the limit price as a numerical value.\n"
                "<i>Example: 104500</i>",
                parse_mode='HTML'
            )
        
        elif state == STATE_AWAITING_TARGET_LIMIT_NUM:
            user_context.temp_data['target_limit_price'] = value
            user_context.conversation_state = None
            
            # Show confirmation
            await _show_target_confirmation(update, user_context)
    
    except Exception as e:
        logger.error(f"Error processing target input: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again or use /start.",
            parse_mode='HTML'
        )

async def handle_target_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle target confirmation - place the order.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    try:
        # Calculate final prices
        entry_price = user_context.temp_data['target_entry_price']
        size = user_context.temp_data['target_size']
        product_id = user_context.temp_data['target_product_id']
        method = user_context.temp_data['target_method']
        
        is_long = size > 0
        
        if method == "percentage":
            trigger_pct = user_context.temp_data['target_trigger_pct']
            limit_pct = user_context.temp_data['target_limit_pct']
            
            stop_price = calculate_target_price_from_percentage(entry_price, trigger_pct, is_long)
            limit_price = calculate_target_price_from_percentage(entry_price, limit_pct, is_long)
        else:
            stop_price = user_context.temp_data['target_trigger_price']
            limit_price = user_context.temp_data['target_limit_price']
        
        # Determine order side (opposite of position)
        order_side = SIDE_SELL if is_long else SIDE_BUY
        
        # Show executing message
        await query.edit_message_text(
            f"{EMOJI_TARGET} <b>Placing Take-Profit Order...</b>\n\n"
            "Please wait...",
            parse_mode='HTML'
        )
        
        # Place take-profit order
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            order_api = OrderAPI(client)
            
            order = order_api.place_take_profit_order(
                product_id=product_id,
                side=order_side,
                size=abs(size),
                stop_price=stop_price,
                limit_price=limit_price,
                reduce_only=True
            )
        
        # Format success message
        success_text = (
            f"{EMOJI_CHECK} <b>Take-Profit Order Placed!</b>\n\n"
            f"<b>Order ID:</b> {order.get('id')}\n"
            f"<b>Product ID:</b> {product_id}\n"
            f"<b>Size:</b> {abs(size)}\n"
            f"<b>Trigger Price:</b> {format_price(stop_price)}\n"
            f"<b>Limit Price:</b> {format_price(limit_price)}\n"
            f"<b>Side:</b> {order_side.upper()}\n\n"
            f"✅ Your take-profit order is now active."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Clear temp data
        user_context.temp_data = {}
        
        logger.info(f"User {user_id} placed take-profit order: {order.get('id')}")
    
    except Exception as e:
        logger.error(f"Error placing take-profit order: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_CROSS} <b>Failed to Place Take-Profit</b>\n\n"
            f"Error: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        user_context.temp_data = {}

async def _show_target_confirmation(update, user_context):
    """
    Show target confirmation message.
    
    Args:
        update: Update object
        user_context: User context
    """
    entry_price = user_context.temp_data['target_entry_price']
    size = user_context.temp_data['target_size']
    method = user_context.temp_data['target_method']
    
    is_long = size > 0
    position_side = "LONG" if is_long else "SHORT"
    
    if method == "percentage":
        trigger_pct = user_context.temp_data['target_trigger_pct']
        limit_pct = user_context.temp_data['target_limit_pct']
        
        stop_price = calculate_target_price_from_percentage(entry_price, trigger_pct, is_long)
        limit_price = calculate_target_price_from_percentage(entry_price, limit_pct, is_long)
        
        confirmation_text = (
            f"{EMOJI_TARGET} <b>Confirm Take-Profit Order</b>\n\n"
            f"<b>Position:</b> {position_side}\n"
            f"<b>Entry Price:</b> {format_price(entry_price)}\n"
            f"<b>Size:</b> {abs(size)}\n\n"
            f"<b>Trigger %:</b> {format_percentage(trigger_pct)}\n"
            f"<b>Trigger Price:</b> {format_price(stop_price)}\n"
            f"<b>Limit %:</b> {format_percentage(limit_pct)}\n"
            f"<b>Limit Price:</b> {format_price(limit_price)}\n\n"
            f"Confirm to place this take-profit order?"
        )
    else:
        stop_price = user_context.temp_data['target_trigger_price']
        limit_price = user_context.temp_data['target_limit_price']
        
        confirmation_text = (
            f"{EMOJI_TARGET} <b>Confirm Take-Profit Order</b>\n\n"
            f"<b>Position:</b> {position_side}\n"
            f"<b>Entry Price:</b> {format_price(entry_price)}\n"
            f"<b>Size:</b> {abs(size)}\n\n"
            f"<b>Trigger Price:</b> {format_price(stop_price)}\n"
            f"<b>Limit Price:</b> {format_price(limit_price)}\n\n"
            f"Confirm to place this take-profit order?"
        )
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI_CHECK} Confirm", callback_data=CALLBACK_CONFIRM_TARGET)],
        [InlineKeyboardButton(f"{EMOJI_CROSS} Cancel", callback_data=CALLBACK_MAIN_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirmation_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
      )
  
