"""Main application entry point with Tornado webhook setup."""
import logging
import asyncio
import json
from typing import Dict, Any

import tornado.ioloop
import tornado.web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config.settings import settings
from config.constants import (
    CALLBACK_SELECT_ACCOUNT, CALLBACK_MAIN_MENU, CALLBACK_ACCOUNT_DETAILS,
    CALLBACK_EXPIRY_SELECTION, CALLBACK_SELECT_ASSET, CALLBACK_SELECT_EXPIRY,
    CALLBACK_SHOW_POSITIONS, CALLBACK_SET_STOPLOSS, CALLBACK_SET_TARGET,
    CALLBACK_MULTI_STOPLOSS, CALLBACK_MULTI_TARGET, CALLBACK_SHOW_ORDERS,
    CALLBACK_BACK_TO_ACCOUNTS, CALLBACK_SELECT_LOT, CALLBACK_CUSTOM_LOT,
    CALLBACK_TRADE_DIRECTION, CALLBACK_CONFIRM_TRADE, CALLBACK_CANCEL_TRADE,
    CALLBACK_SL_POSITION, CALLBACK_SL_METHOD, CALLBACK_CONFIRM_SL,
    CALLBACK_TARGET_POSITION, CALLBACK_TARGET_METHOD, CALLBACK_CONFIRM_TARGET,
    CALLBACK_CANCEL_ORDER, CALLBACK_CANCEL_ALL_ORDERS,
    CALLBACK_MULTI_SL_TOGGLE, CALLBACK_CONFIRM_MULTI_SL,
    CALLBACK_MULTI_TARGET_TOGGLE, CALLBACK_CONFIRM_MULTI_TARGET
)

# Import handlers
from handlers.start import start_command
from handlers.error import error_handler

# Import callbacks
from callbacks.account import (
    handle_account_selection, handle_main_menu, handle_account_details,
    handle_back_to_accounts
)
from callbacks.expiry import (
    handle_expiry_selection, handle_asset_selection, handle_expiry_selected
)
from callbacks.trade import (
    handle_lot_selection,
    handle_custom_lot_callback,
    handle_custom_lot_input,
    handle_trade_direction,
    handle_trade_confirmation
)
from callbacks.position import handle_show_positions
from callbacks.stoploss import (
    handle_set_stoploss,
    handle_stoploss_position_selection,
    handle_stoploss_method_selection,
    handle_stoploss_input,
    handle_stoploss_confirmation,
    handle_multi_stoploss,
    handle_multi_stoploss_toggle,
    handle_multi_stoploss_input,
    handle_multi_stoploss_confirmation
)
from callbacks.target import (
    handle_set_target,
    handle_target_position_selection,
    handle_target_method_selection,
    handle_target_input,
    handle_target_confirmation,
    handle_multi_target,
    handle_multi_target_toggle,
    handle_multi_target_input,
    handle_multi_target_confirmation
)
from callbacks.orders import (
    handle_show_orders,
    handle_cancel_order,
    handle_cancel_all_orders
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Global bot application
bot_application = None

class WebhookHandler(tornado.web.RequestHandler):
    """Tornado request handler for Telegram webhook."""
    
    async def post(self):
        """Handle POST requests from Telegram."""
        try:
            # Parse update from request body
            update_data = json.loads(self.request.body.decode('utf-8'))
            
            # Create Update object
            update = Update.de_json(update_data, bot_application.bot)
            
            # Process update
            await bot_application.process_update(update)
            
            self.set_status(200)
            self.write("OK")
        
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}", exc_info=True)
            self.set_status(500)
            self.write("Error")
    
    def get(self):
        """Handle GET requests for health check."""
        self.set_status(200)
        self.write("Bot is running")

def make_app():
    """Create Tornado application."""
    return tornado.web.Application([
        (r"/", WebhookHandler),
    ])

async def setup_webhook(application: Application):
    """
    Setup webhook for Telegram bot.
    
    Args:
        application: Telegram bot application
    """
    try:
        # Delete existing webhook
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted existing webhook")
        
        # Set new webhook
        webhook_url = settings.WEBHOOK_URL
        await application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        logger.info(f"Webhook set to: {webhook_url}")
        
        # Verify webhook
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        
        if webhook_info.url != webhook_url:
            logger.error(f"Webhook URL mismatch! Expected: {webhook_url}, Got: {webhook_info.url}")
        else:
            logger.info("✅ Webhook successfully configured")
    
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}", exc_info=True)
        raise

def register_handlers(application: Application):
    """
    Register all command and callback handlers.
    
    Args:
        application: Telegram bot application
    """
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Account callbacks
    application.add_handler(CallbackQueryHandler(
        handle_account_selection,
        pattern=f"^{CALLBACK_SELECT_ACCOUNT}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_main_menu,
        pattern=f"^{CALLBACK_MAIN_MENU}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_account_details,
        pattern=f"^{CALLBACK_ACCOUNT_DETAILS}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_back_to_accounts,
        pattern=f"^{CALLBACK_BACK_TO_ACCOUNTS}$"
    ))
    
    # Expiry callbacks
    application.add_handler(CallbackQueryHandler(
        handle_expiry_selection,
        pattern=f"^{CALLBACK_EXPIRY_SELECTION}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_asset_selection,
        pattern=f"^{CALLBACK_SELECT_ASSET}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_expiry_selected,
        pattern=f"^{CALLBACK_SELECT_EXPIRY}:"
    ))
    
    # Trade callbacks
    application.add_handler(CallbackQueryHandler(
        handle_lot_selection,
        pattern=f"^{CALLBACK_SELECT_LOT}:"
    ))
    # Add after handle_lot_selection handler
    application.add_handler(CallbackQueryHandler(
        handle_custom_lot_callback,
        pattern=f"^{CALLBACK_CUSTOM_LOT}$"
    ))

    application.add_handler(CallbackQueryHandler(
        handle_trade_direction,
        pattern=f"^{CALLBACK_TRADE_DIRECTION}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_trade_confirmation,
        pattern=f"^{CALLBACK_CONFIRM_TRADE}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_trade_confirmation,
        pattern=f"^{CALLBACK_CANCEL_TRADE}$"
    ))
    
    # Position callbacks
    application.add_handler(CallbackQueryHandler(
        handle_show_positions,
        pattern=f"^{CALLBACK_SHOW_POSITIONS}$"
    ))
    
    # Stop-loss callbacks
    application.add_handler(CallbackQueryHandler(
        handle_set_stoploss,
        pattern=f"^{CALLBACK_SET_STOPLOSS}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_stoploss_position_selection,
        pattern=f"^{CALLBACK_SL_POSITION}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_stoploss_method_selection,
        pattern=f"^{CALLBACK_SL_METHOD}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_stoploss_confirmation,
        pattern=f"^{CALLBACK_CONFIRM_SL}$"
    ))
    
    # Target callbacks
    application.add_handler(CallbackQueryHandler(
        handle_set_target,
        pattern=f"^{CALLBACK_SET_TARGET}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_target_position_selection,
        pattern=f"^{CALLBACK_TARGET_POSITION}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_target_method_selection,
        pattern=f"^{CALLBACK_TARGET_METHOD}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_target_confirmation,
        pattern=f"^{CALLBACK_CONFIRM_TARGET}$"
    ))
    
    # Orders callbacks
    application.add_handler(CallbackQueryHandler(
        handle_show_orders,
        pattern=f"^{CALLBACK_SHOW_ORDERS}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_cancel_order,
        pattern=f"^{CALLBACK_CANCEL_ORDER}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_cancel_all_orders,
        pattern=f"^{CALLBACK_CANCEL_ALL_ORDERS}$"
    ))
    
    # Message handlers for text input
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_input
    ))

    # Multi-strike stop-loss callbacks
    application.add_handler(CallbackQueryHandler(
        handle_multi_stoploss,
        pattern=f"^{CALLBACK_MULTI_STOPLOSS}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_multi_stoploss_toggle,
        pattern=f"^{CALLBACK_MULTI_SL_TOGGLE}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_multi_stoploss_confirmation,
        pattern=f"^{CALLBACK_CONFIRM_MULTI_SL}$"
    ))

    # Multi-strike target callbacks
    application.add_handler(CallbackQueryHandler(
        handle_multi_target,
        pattern=f"^{CALLBACK_MULTI_TARGET}$"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_multi_target_toggle,
        pattern=f"^{CALLBACK_MULTI_TARGET_TOGGLE}:"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_multi_target_confirmation,
        pattern=f"^{CALLBACK_CONFIRM_MULTI_TARGET}$"
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ All handlers registered")

async def handle_text_input(update: Update, context):
    """
    Route text input to appropriate handler based on conversation state.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    # Import here to avoid circular imports
    from utils.context_manager import UserContextManager
    from config.constants import (
        STATE_AWAITING_CUSTOM_LOT,
        STATE_AWAITING_SL_TRIGGER_PCT, STATE_AWAITING_SL_LIMIT_PCT,
        STATE_AWAITING_SL_TRIGGER_NUM, STATE_AWAITING_SL_LIMIT_NUM,
        STATE_AWAITING_TARGET_TRIGGER_PCT, STATE_AWAITING_TARGET_LIMIT_PCT,
        STATE_AWAITING_TARGET_TRIGGER_NUM, STATE_AWAITING_TARGET_LIMIT_NUM,
        STATE_AWAITING_MULTI_SL_TRIGGER, STATE_AWAITING_MULTI_SL_LIMIT,
        STATE_AWAITING_MULTI_TARGET_TRIGGER, STATE_AWAITING_MULTI_TARGET_LIMIT
    )
    
    context_manager = UserContextManager()
    user_context = context_manager.get_context(update.effective_user.id)
    state = user_context.conversation_state
    
    # Route to appropriate handler
    if state == STATE_AWAITING_CUSTOM_LOT:
        await handle_custom_lot_input(update, context)
    
    elif state in [
        STATE_AWAITING_SL_TRIGGER_PCT, STATE_AWAITING_SL_LIMIT_PCT,
        STATE_AWAITING_SL_TRIGGER_NUM, STATE_AWAITING_SL_LIMIT_NUM
    ]:
        await handle_stoploss_input(update, context)
    
    elif state in [
        STATE_AWAITING_TARGET_TRIGGER_PCT, STATE_AWAITING_TARGET_LIMIT_PCT,
        STATE_AWAITING_TARGET_TRIGGER_NUM, STATE_AWAITING_TARGET_LIMIT_NUM
    ]:
        await handle_target_input(update, context)

    elif state in [STATE_AWAITING_MULTI_SL_TRIGGER, STATE_AWAITING_MULTI_SL_LIMIT]:
        await handle_multi_stoploss_input(update, context)

    elif state in [STATE_AWAITING_MULTI_TARGET_TRIGGER, STATE_AWAITING_MULTI_TARGET_LIMIT]:
        await handle_multi_target_input(update, context)

async def main():
    """Main application entry point."""
    global bot_application
    
    logger.info("🚀 Starting Telegram Delta Exchange Bot")
    logger.info(f"Webhook URL: {settings.WEBHOOK_URL}")
    logger.info(f"Listening on: {settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}")
    
    # Create bot application
    bot_application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Initialize bot
    await bot_application.initialize()
    
    # Register handlers
    register_handlers(bot_application)
    
    # Setup webhook
    await setup_webhook(bot_application)
    
    # Start bot
    await bot_application.start()
    
    # Create Tornado application
    app = make_app()
    app.listen(settings.WEBHOOK_PORT, address=settings.WEBHOOK_HOST)
    
    logger.info(f"✅ Bot is running on {settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}")
    logger.info("Webhook is ready to receive updates from Telegram")
    
    # Keep the application running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
      
