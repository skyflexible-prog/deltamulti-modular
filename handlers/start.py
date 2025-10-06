"""Start command handler."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.accounts import AccountManager
from config.constants import CALLBACK_SELECT_ACCOUNT, EMOJI_ROCKET
from utils.helpers import create_callback_data

logger = logging.getLogger(__name__)

account_manager = AccountManager()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command - Display account selection.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    try:
        # Get all available accounts
        accounts = account_manager.get_all_accounts()
        
        if not accounts:
            await update.message.reply_text(
                "❌ No trading accounts configured. Please contact administrator.",
                parse_mode='HTML'
            )
            return
        
        # Build welcome message
        welcome_text = (
            f"{EMOJI_ROCKET} <b>Welcome to Delta Exchange Trading Bot</b>\n\n"
            f"👤 User: {user.first_name}\n\n"
            f"Please select a trading account to continue:\n"
            f"<i>Choose carefully - each account has different credentials and balances.</i>"
        )
        
        # Build inline keyboard with account buttons
        keyboard = []
        for account in accounts:
            button_text = f"🔑 {account.name}"
            callback_data = create_callback_data(CALLBACK_SELECT_ACCOUNT, account.index)
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"Displayed {len(accounts)} accounts to user {user.id}")
    
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again later.",
            parse_mode='HTML'
        )
      
