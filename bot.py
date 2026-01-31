import re
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
# New Binance SDK for algo orders
from binance_common.configuration import ConfigurationRestAPI
from binance_common.constants import DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
from binance_sdk_derivatives_trading_usds_futures import DerivativesTradingUsdsFutures
from BOTS.BOT_1_P import handle_signal_bot_1_p
from BOTS.BOT_2_BK import handle_signal_bot_2_bk
from BOTS.BOT_3_GG import handle_signal_bot_3_gg
from ADMIN_BOT import handle_admin_command, handle_button_click, send_startup_alert

# Load environment variables from .env file
load_dotenv()

# --- TELEGRAM CONFIG ---
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')

# --- BINANCE CONFIG ---
BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

# --- TESTING CONFIGURATION (2 simple variables) ---
# LISTEN_TO_SIGNAL_GROUP: If true, bot listens to signal channel. If false, listens to private group.
# PLACE_REAL_TRADES: If true, bot places real orders on Binance. If false, only simulates.

LISTEN_TO_SIGNAL_GROUP = os.getenv('LISTEN_TO_SIGNAL_GROUP', 'false').lower() == 'true'
PLACE_REAL_TRADES = os.getenv('PLACE_REAL_TRADES', 'false').lower() == 'true'

# --- BOT 1 (Channel P) CONFIG ---
SIGNAL_CHANNEL_ID_BOT_1_P = int(os.getenv('SIGNAL_CHANNEL_ID_BOT_1_P'))
MY_PRIVATE_GROUP_ID_BOT_1_P = int(os.getenv('MY_PRIVATE_GROUP_ID_BOT_1_P'))
LEVERAGE_BOT_1_P = int(os.getenv('LEVERAGE_BOT_1_P', 5))
MARGIN_USD_BOT_1_P = int(os.getenv('MARGIN_USD_BOT_1_P', 100))

# --- BOT 2 (Channel BK) CONFIG ---
SIGNAL_CHANNEL_ID_BOT_2_BK = int(os.getenv('SIGNAL_CHANNEL_ID_BOT_2_BK'))
MY_PRIVATE_GROUP_ID_BOT_2_BK = int(os.getenv('MY_PRIVATE_GROUP_ID_BOT_2_BK'))
LEVERAGE_BOT_2_BK = int(os.getenv('LEVERAGE_BOT_2_BK', 5))
MARGIN_USD_BOT_2_BK = int(os.getenv('MARGIN_USD_BOT_2_BK', 100))

# --- BOT 3 (Channel GG) CONFIG ---
SIGNAL_CHANNEL_ID_BOT_3_GG = int(os.getenv('SIGNAL_CHANNEL_ID_BOT_3_GG'))
MY_PRIVATE_GROUP_ID_BOT_3_GG = int(os.getenv('MY_PRIVATE_GROUP_ID_BOT_3_GG'))
LEVERAGE_BOT_3_GG = int(os.getenv('LEVERAGE_BOT_3_GG', 5))
MARGIN_USD_BOT_3_GG = int(os.getenv('MARGIN_USD_BOT_3_GG', 100))

# --- ADMIN CONFIG ---
ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID'))
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')  # Bot token from @BotFather

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)

# Initialize Binance client with new SDK
binance_config = ConfigurationRestAPI(
    api_key=BINANCE_KEY,
    api_secret=BINANCE_SECRET,
    base_path=DERIVATIVES_TRADING_USDS_FUTURES_REST_API_PROD_URL
)
binance_client = DerivativesTradingUsdsFutures(config_rest_api=binance_config)

# Admin bot client (separate bot account for buttons)
# Will be initialized in startup_tests() if ADMIN_BOT_TOKEN is set
admin_bot_client = None
HAS_ADMIN_BOT = bool(ADMIN_BOT_TOKEN)

# Cache symbol precision (quantity and price)
SYMBOL_PRECISION = {}  # quantityPrecision
PRICE_PRECISION = {}   # pricePrecision (for tick size)


# =============================================================================
# CENTRALIZED TRADE FUNCTIONS
# =============================================================================

def round_price(price, symbol):
    """Round price to valid tick size for the symbol. Decreases decimal if precision fails."""
    try:
        price_decimals = PRICE_PRECISION.get(symbol, 6)  # Default to 6 if not found
        return round(price, price_decimals)
    except Exception:
        # Fallback: decrease by 1 decimal for safety (e.g., 6 -> 5 decimals)
        fallback_decimals = max(0, PRICE_PRECISION.get(symbol, 6) - 1)
        return round(price, fallback_decimals)


def calculate_quantity(margin_usd, leverage, entry_price, symbol):
    """Calculate quantity based on margin, leverage, and price. Returns basic int if precision fails."""
    try:
        raw_qty = (margin_usd * leverage) / entry_price
        decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price <= 1 else 1)
        quantity = round(raw_qty, decimals)
        if decimals == 0:
            quantity = int(quantity)
        return quantity
    except Exception:
        # Fallback to basic integer calculation
        return int((margin_usd * leverage) / entry_price)


def Enter_Trade(symbol, side, quantity, price, leverage, bot_id):
    """
    Place entry LIMIT order. (Fallback function)
    Returns True if successful, False otherwise.
    """
    try:
        if PLACE_REAL_TRADES:
            # Set Leverage
            binance_client.rest_api.change_initial_leverage(symbol=symbol, leverage=leverage)
            
            # Entry LIMIT Order
            binance_client.rest_api.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                time_in_force='GTC'
            )
            print(f"   [{bot_id}] ✅ Entry order placed: {symbol} {side} @ {price}")
            return True
        else:
            print(f"   [{bot_id}] 🧪 [SIM] Entry order: {symbol} {side} @ {price}")
            return True
    except Exception as e:
        print(f"   [{bot_id}] ⚠️ Entry order error: {str(e)}")
        return False


def TP_Trade(symbol, side, quantity, price, bot_id):
    """
    Place take profit LIMIT order with reduceOnly. (Fallback function - may fail if entry not filled)
    Returns True if successful, False otherwise.
    """
    try:
        if PLACE_REAL_TRADES:
            binance_client.rest_api.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                time_in_force='GTC',
                reduce_only='true'
            )
            print(f"   [{bot_id}] ✅ TP order placed: {symbol} {side} @ {price}")
            return True
        else:
            print(f"   [{bot_id}] 🧪 [SIM] TP order: {symbol} {side} @ {price}")
            return True
    except Exception as e:
        print(f"   [{bot_id}] ⚠️ TP order error: {str(e)}")
        return False


def SL_Trade(symbol, side, quantity, bot_id, executeSL=False, stop_price=None):
    """
    Place stop loss order. (Fallback function - uses algo order now)
    executeSL: If False, skip SL. If True, place SL order.
    Returns True if successful, False otherwise.
    """
    if not executeSL:
        print(f"   [{bot_id}] ℹ️ SL order skipped: {symbol} @ {stop_price}")
        return True
    
    if executeSL:
        try:
            if PLACE_REAL_TRADES:
                # Use algo order for SL (required since Dec 2025)
                binance_client.rest_api.new_algo_order(
                    algo_type="CONDITIONAL",
                    symbol=symbol,
                    side=side,
                    type='STOP_MARKET',
                    trigger_price=stop_price,
                    quantity=quantity,
                    reduce_only='true'
                )
                print(f"   [{bot_id}] ✅ SL order placed: {symbol} {side} @ {stop_price}")
                return True
            else:
                print(f"   [{bot_id}] 🧪 [SIM] SL order: {symbol} {side} @ {stop_price}")
                return True
        except Exception as e:
            print(f"   [{bot_id}] ⚠️ SL order error: {str(e)}")
            return False
    

def Place_Bracket_Order(symbol, side, quantity, entry_price, tp_price, leverage, bot_id, sl_price=None):
    """
    Place Entry + TP + SL using new Algo Order API.
    - Entry: LIMIT order via regular endpoint
    - TP: TAKE_PROFIT_MARKET via algo order with closePosition=true
    - SL: STOP_MARKET via algo order with closePosition=true
    
    Falls back to old method (Enter_Trade + TP_Trade + SL_Trade) if new method fails.
    
    Returns: (success, result_or_error)
    """
    exit_side = "SELL" if side == "BUY" else "BUY"
    
    try:
        if PLACE_REAL_TRADES:
            # Step 1: Set leverage
            binance_client.rest_api.change_initial_leverage(symbol=symbol, leverage=leverage)
            
            # Step 2: Place Entry LIMIT order
            entry_result = binance_client.rest_api.new_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                price=entry_price,
                time_in_force="GTC"
            )
            print(f"   [{bot_id}] ✅ Entry order placed: {symbol} {side} @ {entry_price}")
            
            # Step 3: Place TP (algo order with closePosition)
            tp_result = binance_client.rest_api.new_algo_order(
                algo_type="CONDITIONAL",
                symbol=symbol,
                side=exit_side,
                type="TAKE_PROFIT_MARKET",
                trigger_price=tp_price,
                close_position="true"
            )
            print(f"   [{bot_id}] ✅ TP algo order placed: {symbol} {exit_side} @ trigger {tp_price}")
            
            # Step 4: Place SL if provided (algo order with closePosition)
            if sl_price:
                sl_result = binance_client.rest_api.new_algo_order(
                    algo_type="CONDITIONAL",
                    symbol=symbol,
                    side=exit_side,
                    type="STOP_MARKET",
                    trigger_price=sl_price,
                    close_position="true"
                )
                print(f"   [{bot_id}] ✅ SL algo order placed: {symbol} {exit_side} @ trigger {sl_price}")
            
            print(f"   [{bot_id}] ✅ Bracket order complete: {symbol} {side} @ {entry_price} | TP: {tp_price} | SL: {sl_price}")
            return True, entry_result
        else:
            print(f"   [{bot_id}] 🧪 [SIM] Bracket order: {symbol} {side} @ {entry_price} | TP: {tp_price} | SL: {sl_price}")
            return True, None
    except Exception as e:
        print(f"   [{bot_id}] ⚠️ Algo order failed: {str(e)}")
        print(f"   [{bot_id}] ⚠️ Falling back to old method...")
        # Fallback to existing Enter_Trade, TP_Trade, SL_Trade
        entry_success = Enter_Trade(symbol, side, quantity, entry_price, leverage, bot_id)
        if entry_success:
            TP_Trade(symbol, exit_side, quantity, tp_price, bot_id)
            if sl_price:
                SL_Trade(symbol, exit_side, quantity, bot_id, executeSL=True, stop_price=sl_price)
        return False, str(e)


# =============================================================================
# STARTUP TESTS
# =============================================================================

async def test_channel_ids():
    """
    Test all 4 channel/group IDs to verify Telegram access.
    Exits the bot if any channel fails.
    """
    channels_to_test = [
        (SIGNAL_CHANNEL_ID_BOT_1_P, "Signal Channel BOT_1_P"),
        (MY_PRIVATE_GROUP_ID_BOT_1_P, "Private Group BOT_1_P"),
        (SIGNAL_CHANNEL_ID_BOT_2_BK, "Signal Channel BOT_2_BK"),
        (MY_PRIVATE_GROUP_ID_BOT_2_BK, "Private Group BOT_2_BK"),
        (SIGNAL_CHANNEL_ID_BOT_3_GG, "Signal Channel BOT_3_GG"),
        (MY_PRIVATE_GROUP_ID_BOT_3_GG, "Private Group BOT_3_GG"),
    ]
    
    for channel_id, channel_name in channels_to_test:
        try:
            entity = await tg_client.get_entity(channel_id)
            # Use end=' | ' for Signal channels to combine with Private on same line
            if "Signal" in channel_name:
                print(f"[BOT]    {channel_name}: ✅", end=' | ')
            else:
                print(f"{channel_name}: ✅")
        except Exception as e:
            print(f"[BOT]    ❌ {channel_name}: FAILED - {str(e)}")


async def startup_tests():
    """Run tests on startup to verify Telegram and Binance access"""
    
    # Print Telegram account
    me = await tg_client.get_me()
    print(f"[BOT]    Telegram account: {me.first_name}")
    
    # Test all 4 channel/group IDs
    await test_channel_ids()
    
    # Test Binance API connection with private endpoint (verifies IP whitelist)
    try:
        response = binance_client.rest_api.account_information_v2()
        account = response.data()
        wallet_balance = float(account.total_wallet_balance if hasattr(account, 'total_wallet_balance') else account.get('totalWalletBalance', 0))
        print(f"[BOT]    Binance API: ✅ Connected (Balance: {wallet_balance:.2f} USDT)")
        
        # Validate margin settings against wallet balance
        if MARGIN_USD_BOT_1_P > wallet_balance:
            print(f"[BOT]    ⚠️ MARGIN_USD_BOT_1_P (${MARGIN_USD_BOT_1_P}) > Balance (${wallet_balance:.2f})", end = ' | ')
        else:
            print(f"[BOT]    BOT_1_P Margin: ✅ ${MARGIN_USD_BOT_1_P} < Balance", end = ' | ')
        
        if MARGIN_USD_BOT_2_BK > wallet_balance:
            print(f"[BOT]    ⚠️ MARGIN_USD_BOT_2_BK (${MARGIN_USD_BOT_2_BK}) > Balance (${wallet_balance:.2f})", end = ' | ')
        else:
            print(f"[BOT]    BOT_2_BK Margin: ✅ ${MARGIN_USD_BOT_2_BK} < Balance", end = ' | ')
        
        if MARGIN_USD_BOT_3_GG > wallet_balance:
            print(f"[BOT]    ⚠️ MARGIN_USD_BOT_3_GG (${MARGIN_USD_BOT_3_GG}) > Balance (${wallet_balance:.2f})")
        else:
            print(f"BOT_3_GG Margin: ✅ ${MARGIN_USD_BOT_3_GG} < Balance")
            
    except Exception as e:
        print(f"[BOT]    ❌ Binance API: FAILED - {str(e)}")
        print(f"[BOT]    Check: API key, IP whitelist, Futures enabled")
    
    # Cache symbol precision
    global SYMBOL_PRECISION, PRICE_PRECISION
    try:
        response = binance_client.rest_api.exchange_information()
        exchange_info = response.data()
        symbols_list = exchange_info.symbols if hasattr(exchange_info, 'symbols') else []
        for s in symbols_list:
            sym = s.symbol if hasattr(s, 'symbol') else s.get('symbol', '')
            qty_prec = s.quantity_precision if hasattr(s, 'quantity_precision') else s.get('quantity_precision', 0)
            price_prec = s.price_precision if hasattr(s, 'price_precision') else s.get('price_precision', 0)
            SYMBOL_PRECISION[sym] = qty_prec
            PRICE_PRECISION[sym] = price_prec
        print(f"[BOT]    Binance Symbols: ✅ Cached {len(SYMBOL_PRECISION)} symbols", '========================')
    except Exception as e:
        print(f"[BOT]    ⚠️ Could not cache decimals: {str(e)}")
    
    # Register event handlers
    # Determine listen channels based on LISTEN_TO_SIGNAL_GROUP
    listen_channel_bot_1_p = SIGNAL_CHANNEL_ID_BOT_1_P if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID_BOT_1_P
    listen_channel_bot_2_bk = SIGNAL_CHANNEL_ID_BOT_2_BK if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID_BOT_2_BK
    listen_channel_bot_3_gg = SIGNAL_CHANNEL_ID_BOT_3_GG if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID_BOT_3_GG
    
    # Create config objects to pass to handlers
    config_bot_1_p = {
        'bot_id': 'BOT_1_P',
        'leverage': LEVERAGE_BOT_1_P,
        'margin_usd': MARGIN_USD_BOT_1_P,
        'private_group_id': MY_PRIVATE_GROUP_ID_BOT_1_P
    }
    
    config_bot_2_bk = {
        'bot_id': 'BOT_2_BK',
        'leverage': LEVERAGE_BOT_2_BK,
        'margin_usd': MARGIN_USD_BOT_2_BK,
        'private_group_id': MY_PRIVATE_GROUP_ID_BOT_2_BK
    }
    
    config_bot_3_gg = {
        'bot_id': 'BOT_3_GG',
        'leverage': LEVERAGE_BOT_3_GG,
        'margin_usd': MARGIN_USD_BOT_3_GG,
        'private_group_id': MY_PRIVATE_GROUP_ID_BOT_3_GG
    }
    
    precision = {
        'symbol': SYMBOL_PRECISION,
        'price': PRICE_PRECISION
    }
    
    # Register handlers with wrappers to pass config
    # outgoing=False prevents race condition when testing (bot won't react to its own messages)
    @tg_client.on(events.NewMessage(chats=listen_channel_bot_1_p))
    async def wrapper_bot_1_p(event):
        await handle_signal_bot_1_p(event, tg_client, binance_client, config_bot_1_p, precision,
                                     Enter_Trade, TP_Trade, SL_Trade, Place_Bracket_Order,round_price, calculate_quantity,
                                     PLACE_REAL_TRADES)
    
    @tg_client.on(events.NewMessage(chats=listen_channel_bot_2_bk))
    async def wrapper_bot_2_bk(event):
        await handle_signal_bot_2_bk(event, tg_client, binance_client, config_bot_2_bk, precision,
                                      Enter_Trade, TP_Trade, SL_Trade, Place_Bracket_Order, round_price, calculate_quantity,
                                      PLACE_REAL_TRADES)
    
    @tg_client.on(events.NewMessage(chats=listen_channel_bot_3_gg))
    async def wrapper_bot_3_gg(event):
        await handle_signal_bot_3_gg(event, tg_client, binance_client, config_bot_3_gg, precision,
                                      Enter_Trade, TP_Trade, SL_Trade, Place_Bracket_Order, round_price, calculate_quantity,
                                      PLACE_REAL_TRADES)
    
    # Initialize admin bot client if token is set
    global admin_bot_client
    if HAS_ADMIN_BOT and admin_bot_client is None:
        try:
            admin_bot_client = TelegramClient('admin_bot', TELEGRAM_API_ID, TELEGRAM_API_HASH)
            await admin_bot_client.start(bot_token=ADMIN_BOT_TOKEN)
            print("[ADMIN] ✅ Bot account connected (buttons enabled!)")
        except Exception as e:
            print(f"[ADMIN] ❌ Failed to connect bot account: {e}")
            admin_bot_client = None
    elif not HAS_ADMIN_BOT:
        print("[ADMIN] ℹ️ No ADMIN_BOT_TOKEN - using text commands only")
    
    # Admin handler - use bot client if available (for buttons!)
    admin_client = admin_bot_client if admin_bot_client else tg_client
    admin_config = {'admin_group_id': ADMIN_GROUP_ID, 'has_buttons': admin_bot_client is not None}
    
    # Register handlers on the appropriate client
    if admin_bot_client:
        # Bot account - register on bot client
        @admin_bot_client.on(events.NewMessage(chats=ADMIN_GROUP_ID))
        async def wrapper_admin(event):
            await handle_admin_command(event, admin_bot_client, admin_config)
        
        @admin_bot_client.on(events.CallbackQuery())
        async def wrapper_admin_buttons(event):
            if event.chat_id == ADMIN_GROUP_ID:
                await handle_button_click(event, admin_bot_client, admin_config)
    else:
        # User account fallback - register on user client
        @tg_client.on(events.NewMessage(chats=ADMIN_GROUP_ID))
        async def wrapper_admin(event):
            await handle_admin_command(event, tg_client, admin_config)
    
    # Send startup alert
    await send_startup_alert(admin_client, ADMIN_GROUP_ID, admin_config.get('has_buttons', False))


# =============================================================================
# STARTUP LOGIC
# =============================================================================

if __name__ == "__main__":
    
    # Determine listening sources
    bot_1_p_source = "✅Signal Channel" if LISTEN_TO_SIGNAL_GROUP else "❌Private Group"
    bot_2_bk_source = "✅Signal Channel" if LISTEN_TO_SIGNAL_GROUP else "❌Private Group"
    bot_3_gg_source = "✅Signal Channel" if LISTEN_TO_SIGNAL_GROUP else "❌Private Group"
    
    print(f"[BOT] 📡 Listening to: {{'BOT_1_P': '{bot_1_p_source}', 'BOT_2_BK': '{bot_2_bk_source}', 'BOT_3_GG': '{bot_3_gg_source}'}} ========================")
    print(f"[BOT] 💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")
    print(f"[BOT]    BOT_1_P - Leverage: {LEVERAGE_BOT_1_P}x | Margin: ${MARGIN_USD_BOT_1_P} | BOT_2_BK - Leverage: {LEVERAGE_BOT_2_BK}x | Margin: ${MARGIN_USD_BOT_2_BK} | BOT_3_GG - Leverage: {LEVERAGE_BOT_3_GG}x | Margin: ${MARGIN_USD_BOT_3_GG}")
    
    tg_client.start()
    tg_client.loop.run_until_complete(startup_tests())
    tg_client.run_until_disconnected()
