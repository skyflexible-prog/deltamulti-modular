"""Expiry selection callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from config.constants import (
    CALLBACK_SELECT_ASSET, CALLBACK_SELECT_EXPIRY, CALLBACK_MAIN_MENU,
    CALLBACK_EXPIRY_SELECTION,  # Add this line
    ASSET_BTC, ASSET_ETH, EMOJI_CHART
)
from delta_api.client import DeltaClient
from delta_api.products import ProductAPI
from utils.helpers import create_callback_data, parse_callback_data, chunk_list
from utils.formatters import format_datetime, format_straddle_details
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

context_manager = UserContextManager()

async def handle_expiry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle expiry selection menu - ask for underlying asset.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    # Better check for account
    if not user_context.has_account():
        logger.warning(f"User {user_id} tried to access expiry selection without account")
        logger.debug(f"Context state: account_credentials={user_context.account_credentials}")
        
        await query.edit_message_text(
            "❌ No account selected. Please use /start to select an account.",
            parse_mode='HTML'
        )
        return

    logger.info(f"User {user_id} accessing expiry selection with account {user_context.account_name}")
    
    # Clear previous trade data
    user_context.clear_trade_data()
    
    # Build asset selection keyboard
    keyboard = [
        [InlineKeyboardButton(
            "₿ BTCUSD",
            callback_data=create_callback_data(CALLBACK_SELECT_ASSET, ASSET_BTC)
        )],
        [InlineKeyboardButton(
            "Ξ ETHUSD",
            callback_data=create_callback_data(CALLBACK_SELECT_ASSET, ASSET_ETH)
        )],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=CALLBACK_MAIN_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{EMOJI_CHART} <b>Select Underlying Asset:</b>\n\n"
        "Choose the asset for options trading:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_asset_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle asset selection - fetch and display available expiries.
    
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
        # Extract asset from callback
        asset = callback_data['params'][0]
        user_context.selected_asset = asset
        
        logger.info(f"User {user_id} selected asset: {asset}")
        
        # Show loading message
        await query.edit_message_text(
            f"⏳ Fetching available expiries for <b>{asset}</b>...",
            parse_mode='HTML'
        )
        
        # Fetch available expiries
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            product_api = ProductAPI(client)
            expiries = product_api.get_available_expiries(asset)
        
        if not expiries:
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_EXPIRY_SELECTION)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"❌ No expiries available for {asset}.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Build expiry selection keyboard (limited to first 10 expiries)
        keyboard = []
        for expiry in expiries[:10]:  # Limit to avoid message too long
            expiry_dt = expiry['datetime']
            button_text = expiry_dt.strftime("%d %b %Y %H:%M")
            callback_data_str = create_callback_data(
                CALLBACK_SELECT_EXPIRY,
                asset,
                expiry['timestamp']
            )
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data_str)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_EXPIRY_SELECTION)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{EMOJI_CHART} <b>Select Expiry for {asset}:</b>\n\n"
            f"Available expiries (sorted by date):",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error fetching expiries: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_EXPIRY_SELECTION)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch expiries.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_expiry_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle expiry selection - display ATM straddle details and lot selection.
    
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
        # Extract asset and expiry from callback
        asset = callback_data['params'][0]
        expiry_timestamp = int(callback_data['params'][1])
        
        user_context.selected_asset = asset
        user_context.selected_expiry = expiry_timestamp
        
        logger.info(f"User {user_id} selected expiry: {expiry_timestamp}")
        
        # Show loading message
        await query.edit_message_text(
            f"⏳ Fetching ATM options for <b>{asset}</b>...",
            parse_mode='HTML'
        )
        
        # Fetch spot price and ATM options
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            product_api = ProductAPI(client)
            
            # Get spot price
            spot_price = product_api.get_spot_price(asset)
            
            # Find ATM options
            atm_options = product_api.find_atm_options(asset, expiry_timestamp, spot_price)
        
        # Store options data
        user_context.selected_strike = atm_options['atm_strike']
        user_context.call_product_id = atm_options['call']['product_id']
        user_context.put_product_id = atm_options['put']['product_id']
        
        # Format straddle details
        expiry_dt = datetime.fromtimestamp(expiry_timestamp)
        details_text = format_straddle_details(
            asset,
            expiry_dt,
            spot_price,
            atm_options['atm_strike'],
            atm_options['call'],
            atm_options['put']
        )
        
        # Build lot selection keyboard
        from config.constants import PREDEFINED_LOTS, CALLBACK_SELECT_LOT, CALLBACK_CUSTOM_LOT
        keyboard = []
        for lot in PREDEFINED_LOTS:
            keyboard.append([InlineKeyboardButton(
                f"{lot} Lot{'s' if lot > 1 else ''}",
                callback_data=create_callback_data(CALLBACK_SELECT_LOT, lot)
            )])
        keyboard.append([InlineKeyboardButton(
            "✏️ Custom Lot",
            callback_data=CALLBACK_CUSTOM_LOT
        )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_EXPIRY_SELECTION)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            details_text + "\n\n<b>Select Lot Size:</b>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Error fetching ATM options: {e}", exc_info=True)
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=CALLBACK_EXPIRY_SELECTION)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch ATM options.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
      )
          
