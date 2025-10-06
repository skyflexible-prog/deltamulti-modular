"""Account-related callback handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.accounts import AccountManager
from config.constants import (
    CALLBACK_MAIN_MENU, CALLBACK_ACCOUNT_DETAILS, CALLBACK_EXPIRY_SELECTION,
    CALLBACK_SHOW_POSITIONS, CALLBACK_SET_STOPLOSS, CALLBACK_SET_TARGET,
    CALLBACK_MULTI_STOPLOSS, CALLBACK_MULTI_TARGET, CALLBACK_SHOW_ORDERS,
    CALLBACK_BACK_TO_ACCOUNTS, EMOJI_MONEY, EMOJI_CHART, EMOJI_SHIELD,
    EMOJI_TARGET, EMOJI_WARNING
)
from delta_api.client import DeltaClient
from delta_api.wallet import WalletAPI
from utils.helpers import create_callback_data, parse_callback_data
from utils.formatters import format_account_summary
from utils.context_manager import UserContextManager

logger = logging.getLogger(__name__)

account_manager = AccountManager()
context_manager = UserContextManager()

async def handle_account_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle account selection callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = parse_callback_data(query.data)
    
    try:
        # Extract account index from callback data
        account_index = int(callback_data['params'][0])
        
        # Get account from manager
        account = account_manager.get_account(account_index)
        if not account:
            await query.edit_message_text(
                "❌ Invalid account selection. Please try again.",
                parse_mode='HTML'
            )
            return
        
        # Store account in user context WITH name and description
        user_context = context_manager.get_context(user_id)
        user_context.set_account(
            account_index, 
            account.api_key, 
            account.api_secret,
            account.name,
            account.description
        )
        
        logger.info(f"User {user_id} selected account: {account.name} (index={account_index})")
        logger.debug(f"Account credentials stored: api_key={account.api_key[:10]}...")
        
        # Fetch account balance
        loading_message = await query.edit_message_text(
            f"⏳ Loading account details for <b>{account.name}</b>...",
            parse_mode='HTML'
        )
        
        try:
            # Create Delta client with account credentials
            with DeltaClient(account.api_key, account.api_secret) as client:
                wallet_api = WalletAPI(client)
                account_summary = wallet_api.get_account_summary()
            
            # Format and display account details
            summary_text = format_account_summary(
                account_summary,
                account.name,
                account.description
            )
            
            # Display main menu
            keyboard = _build_main_menu_keyboard()
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await loading_message.edit_text(
                summary_text + "\n\n<b>📋 Main Menu:</b>\nSelect an option below:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

            logger.info(f"User {user_id} successfully loaded account {account.name}")
        
        except Exception as e:
            logger.error(f"Failed to fetch account details: {e}", exc_info=True)
            await loading_message.edit_text(
                f"❌ Failed to fetch account details for <b>{account.name}</b>.\n"
                f"Error: {str(e)}\n\n"
                f"Please check your API credentials and try again.",
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Error in account selection: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try /start again.",
            parse_mode='HTML'
        )

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle main menu callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_context = context_manager.get_context(user_id)
    
    # Verify account is selected
    if not user_context.account_credentials:
        await query.edit_message_text(
            "❌ No account selected. Please use /start to select an account.",
            parse_mode='HTML'
        )
        return
    
    # Clear trade data but keep account selection
    user_context.clear_trade_data()
    user_context.conversation_state = None
    
    # Get account info
    account = account_manager.get_account(user_context.account_index)
    
    # Build main menu
    keyboard = _build_main_menu_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{EMOJI_MONEY} <b>{account.name}</b>\n\n"
        f"<b>📋 Main Menu:</b>\nSelect an option below:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_account_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle account details callback.
    
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
    
    # Get account info
    account = account_manager.get_account(user_context.account_index)
    
    # Show loading message
    await query.edit_message_text(
        f"⏳ Fetching account details for <b>{account.name}</b>...",
        parse_mode='HTML'
    )
    
    try:
        # Create Delta client with stored credentials
        with DeltaClient(
            user_context.account_credentials['api_key'],
            user_context.account_credentials['api_secret']
        ) as client:
            wallet_api = WalletAPI(client)
            account_summary = wallet_api.get_account_summary()
        
        # Format account details
        summary_text = format_account_summary(
            account_summary,
            account.name,
            account.description
        )
        
        # Add back button
        keyboard = [[
            InlineKeyboardButton(
                "🔙 Back to Main Menu",
                callback_data=CALLBACK_MAIN_MENU
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            summary_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    except Exception as e:
        logger.error(f"Failed to fetch account details: {e}", exc_info=True)
        
        keyboard = [[
            InlineKeyboardButton(
                "🔙 Back to Main Menu",
                callback_data=CALLBACK_MAIN_MENU
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Failed to fetch account details.\nError: {str(e)}",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def handle_back_to_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle back to account selection callback.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Clear user context
    context_manager.clear_context(user_id)
    
    # Get all available accounts
    accounts = account_manager.get_all_accounts()
    
    # Build account selection keyboard
    keyboard = []
    for account in accounts:
        button_text = f"🔑 {account.name}"
        callback_data = create_callback_data('select_account', account.index)
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔑 <b>Select Trading Account:</b>\n\n"
        "<i>Choose the account you want to trade with.</i>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

def _build_main_menu_keyboard():
    """
    Build main menu inline keyboard.
    
    Returns:
        List of keyboard button rows
    """
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI_CHART} Account Details", callback_data=CALLBACK_ACCOUNT_DETAILS)],
        [InlineKeyboardButton(f"📅 Expiry Selection", callback_data=CALLBACK_EXPIRY_SELECTION)],
        [InlineKeyboardButton(f"{EMOJI_CHART} Show Positions", callback_data=CALLBACK_SHOW_POSITIONS)],
        [InlineKeyboardButton(f"{EMOJI_SHIELD} Set Stop-Loss", callback_data=CALLBACK_SET_STOPLOSS)],
        [InlineKeyboardButton(f"{EMOJI_TARGET} Set Targets", callback_data=CALLBACK_SET_TARGET)],
        [InlineKeyboardButton(f"{EMOJI_SHIELD} Multi-Strike Stop-Loss", callback_data=CALLBACK_MULTI_STOPLOSS)],
        [InlineKeyboardButton(f"{EMOJI_TARGET} Multi-Strike Targets", callback_data=CALLBACK_MULTI_TARGET)],
        [InlineKeyboardButton(f"{EMOJI_WARNING} Show Orders", callback_data=CALLBACK_SHOW_ORDERS)],
        [InlineKeyboardButton("🔄 Change Account", callback_data=CALLBACK_BACK_TO_ACCOUNTS)]
    ]
    return keyboard
      
