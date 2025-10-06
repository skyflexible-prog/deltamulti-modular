"""Application constants."""

# Callback Data Prefixes
CALLBACK_SELECT_ACCOUNT = "select_account"
CALLBACK_MAIN_MENU = "main_menu"
CALLBACK_ACCOUNT_DETAILS = "account_details"
CALLBACK_EXPIRY_SELECTION = "expiry_selection"
CALLBACK_SELECT_ASSET = "select_asset"
CALLBACK_SELECT_EXPIRY = "select_expiry"
CALLBACK_SHOW_POSITIONS = "show_positions"
CALLBACK_SET_STOPLOSS = "set_stoploss"
CALLBACK_SET_TARGET = "set_target"
CALLBACK_MULTI_STOPLOSS = "multi_stoploss"
CALLBACK_MULTI_TARGET = "multi_target"
CALLBACK_SHOW_ORDERS = "show_orders"
CALLBACK_BACK_TO_ACCOUNTS = "back_to_accounts"
CALLBACK_BACK_TO_MAIN = "back_to_main"
CALLBACK_SELECT_LOT = "select_lot"
CALLBACK_CUSTOM_LOT = "custom_lot"
CALLBACK_TRADE_DIRECTION = "trade_direction"
CALLBACK_CONFIRM_TRADE = "confirm_trade"
CALLBACK_CANCEL_TRADE = "cancel_trade"
CALLBACK_SL_POSITION = "sl_position"
CALLBACK_TARGET_POSITION = "target_position"
CALLBACK_SL_METHOD = "sl_method"
CALLBACK_TARGET_METHOD = "target_method"
CALLBACK_CONFIRM_SL = "confirm_sl"
CALLBACK_CONFIRM_TARGET = "confirm_target"
CALLBACK_MULTI_SL_TOGGLE = "multi_sl_toggle"
CALLBACK_MULTI_TARGET_TOGGLE = "multi_target_toggle"
CALLBACK_CONFIRM_MULTI_SL = "confirm_multi_sl"
CALLBACK_CONFIRM_MULTI_TARGET = "confirm_multi_target"
CALLBACK_CANCEL_ORDER = "cancel_order"
CALLBACK_CANCEL_ALL_ORDERS = "cancel_all_orders"

# Conversation States
STATE_AWAITING_CUSTOM_LOT = "awaiting_custom_lot"
STATE_AWAITING_SL_TRIGGER_PCT = "awaiting_sl_trigger_pct"
STATE_AWAITING_SL_LIMIT_PCT = "awaiting_sl_limit_pct"
STATE_AWAITING_SL_TRIGGER_NUM = "awaiting_sl_trigger_num"
STATE_AWAITING_SL_LIMIT_NUM = "awaiting_sl_limit_num"
STATE_AWAITING_TARGET_TRIGGER_PCT = "awaiting_target_trigger_pct"
STATE_AWAITING_TARGET_LIMIT_PCT = "awaiting_target_limit_pct"
STATE_AWAITING_TARGET_TRIGGER_NUM = "awaiting_target_trigger_num"
STATE_AWAITING_TARGET_LIMIT_NUM = "awaiting_target_limit_num"
STATE_AWAITING_MULTI_SL_TRIGGER = "awaiting_multi_sl_trigger"
STATE_AWAITING_MULTI_SL_LIMIT = "awaiting_multi_sl_limit"
STATE_AWAITING_MULTI_TARGET_TRIGGER = "awaiting_multi_target_trigger"
STATE_AWAITING_MULTI_TARGET_LIMIT = "awaiting_multi_target_limit"

# Underlying Assets
ASSET_BTC = "BTCUSD"
ASSET_ETH = "ETHUSD"
UNDERLYING_SYMBOLS = {
    ASSET_BTC: "BTC",
    ASSET_ETH: "ETH"
}

# Order Types
ORDER_TYPE_MARKET = "market_order"
ORDER_TYPE_LIMIT = "limit_order"
STOP_ORDER_TYPE_SL = "stop_loss_order"
STOP_ORDER_TYPE_TP = "take_profit_order"

# Order Sides
SIDE_BUY = "buy"
SIDE_SELL = "sell"

# Trade Directions
DIRECTION_LONG = "long"
DIRECTION_SHORT = "short"

# Predefined Lot Sizes
PREDEFINED_LOTS = [1, 2, 5, 10]

# Contract Types
CONTRACT_TYPE_CALL = "call_options"
CONTRACT_TYPE_PUT = "put_options"

# Order States
ORDER_STATE_OPEN = "open"
ORDER_STATE_PENDING = "pending"

# Emojis
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_CHART = "📊"
EMOJI_MONEY = "💰"
EMOJI_WARNING = "⚠️"
EMOJI_CLOCK = "🕐"
EMOJI_ROCKET = "🚀"
EMOJI_TARGET = "🎯"
EMOJI_SHIELD = "🛡️"
