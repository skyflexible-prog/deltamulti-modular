"""Order management callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.constants import (
    CALLBACK_SHOW_ORDERS, CALLBACK_CANCEL_ORDER, CALLBACK_CANCEL_ALL_ORDERS,
    CALLBACK_MAIN_MENU, EMOJI_WARNING, EMOJI_CHECK, EMOJI_CROSS,
    ORDER_STATE_OPEN, ORDER_STATE_PENDING
)
from delta_api.client import DeltaClient
from delta_api.orders import OrderAPI
from utils.helpers import create_callback_data, parse_callback_data
from utils.formatters import format_order
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

context_manager = UserContextManager()

async def handle_show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle show orders callback - display all open and pending orders.
    
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
        "⏳ Fetching orders...",
        parse_mode='HTML'
    )
    
    try:
        # Fetch both open and pending orders
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            order_api = OrderAPI(client)
            
            open_orders = order_api.get_open_orders()
            pending_orders = order_api.get_pending_orders()
        
        all_orders = open_orders + pending_orders
        
        if not all_orders:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"{EMOJI_WARNING} <b>Orders</b>\n\n"
                "You have no open or pending orders.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Format orders
        orders_text = f"{EMOJI_WARNING} <b>Your Orders</b>\n\n"
        
        # Group by type
        if open_orders:
            orders_text += f"<b>📋 Open Orders ({len(open_orders)}):</b>\n"
            for i, order in enumerate(open_orders, 1):
                orders_text += f"\n<b>Order {i}:</b>\n"
                orders_text += format_order(order)
                orders_text += f"\nOrder ID: {order['id']}\n"
        
        if pending_orders:
            orders_text += f"\n<b>⏳ Pending Stop Orders ({len(pending_orders)}):</b>\n"
            for i, order in enumerate(pending_orders, 1):
                orders_text += f"\n<b>Order {i}:</b>\n"
                orders_text += format_order(order)
                orders_text += f"\nOrder ID: {order['id']}\n"
        
        # Build keyboard with cancel options
        keyboard = []
        
        # Add individual cancel buttons (limit to first 5 orders to avoid message too long)
        for order in all_orders[:5]:
            button_text = f"❌ Cancel {order['symbol'][:10]}"
            callback_data = create_callback_data(CALLBACK_CANCEL_ORDER, order['id'])
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add cancel all button
        keyboard.append([InlineKeyboardButton(
            "🗑️ Cancel All Orders",
            callback_data=CALLBACK_CANCEL_ALL_ORDERS
        )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            orders_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error fetching orders: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch orders.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle cancel individual order callback.
    
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
        # Extract order ID
        order_id = int(callback_data['params'][0])
        
        # Show cancelling message
        await query.edit_message_text(
            f"⏳ Cancelling order {order_id}...",
            parse_mode='HTML'
        )
        
        # Cancel the order
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            order_api = OrderAPI(client)
            result = order_api.cancel_order(order_id)
        
        success_text = (
            f"{EMOJI_CHECK} <b>Order Cancelled</b>\n\n"
            f"Order ID <code>{order_id}</code> has been cancelled successfully."
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 View Orders", callback_data=CALLBACK_SHOW_ORDERS)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"User {user_id} cancelled order {order_id}")
    
    except Exception as e:
        logger.error(f"Error cancelling order: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_CROSS} <b>Failed to Cancel Order</b>\n\n"
            f"Error: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_cancel_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle cancel all orders callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    try:
        # Show cancelling message
        await query.edit_message_text(
            "⏳ Cancelling all orders...",
            parse_mode='HTML'
        )
        
        # Cancel all orders
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            order_api = OrderAPI(client)
            result = order_api.cancel_all_orders()
        
        success_text = (
            f"{EMOJI_CHECK} <b>All Orders Cancelled</b>\n\n"
            f"All your open and pending orders have been cancelled successfully."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"User {user_id} cancelled all orders")
    
    except Exception as e:
        logger.error(f"Error cancelling all orders: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_CROSS} <b>Failed to Cancel All Orders</b>\n\n"
            f"Error: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
      
