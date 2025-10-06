"""Error handler for bot exceptions."""
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors in the bot.
    
    Args:
        update: Telegram update object
        context: Callback context with error info
    """
    # Log the error
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Log full traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    logger.error(f"Traceback:\n{tb_string}")
    
    # Notify user
    try:
        if update and update.effective_message:
            error_message = (
                "❌ <b>An error occurred</b>\n\n"
                "Sorry, something went wrong while processing your request. "
                "Please try again or contact support if the issue persists."
            )
            await update.effective_message.reply_text(
                error_message,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error sending error message to user: {e}")
      
