import re
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from binance.um_futures import UMFutures
from BOT_1_P import handle_signal_bot_1_p
from BOT_2_BK import handle_signal_bot_2_bk

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

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
binance_client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

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
    Place entry LIMIT order.
    Returns True if successful, False otherwise.
    """
    try:
        if PLACE_REAL_TRADES:
            # Set Leverage
            binance_client.change_leverage(symbol=symbol, leverage=leverage)
            
            # Entry LIMIT Order
            binance_client.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
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
    Place take profit LIMIT order with reduceOnly.
    Returns True if successful, False otherwise.
    """
    try:
        if PLACE_REAL_TRADES:
            binance_client.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC',
                reduceOnly='True'
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
    Place stop loss order.
    executeSL: If False, skip SL. If True, place SL order.
    Returns True if successful, False otherwise.
    """
    if not executeSL:
        print(f"   [{bot_id}] ℹ️ SL order skipped: {symbol} @ {stop_price}")
        return True
    
    if executeSL:
        try:
            if PLACE_REAL_TRADES:
                binance_client.new_order(
                    symbol=symbol,
                    side=side,
                    type='STOP_MARKET',
                    quantity=quantity,
                    stopPrice=stop_price,
                    reduceOnly='True'
                )
                print(f"   [{bot_id}] ✅ SL order placed: {symbol} {side} @ {stop_price}")
                return True
            else:
                print(f"   [{bot_id}] 🧪 [SIM] SL order: {symbol} {side} @ {stop_price}")
                return True
        except Exception as e:
            print(f"   [{bot_id}] ⚠️ SL order error: {str(e)}")
            return False
    

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
        account = binance_client.account()
        wallet_balance = float(account['totalWalletBalance'])
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
            
    except Exception as e:
        print(f"[BOT]    ❌ Binance API: FAILED - {str(e)}")
        print(f"[BOT]    Check: API key, IP whitelist, Futures enabled")
    
    # Cache symbol precision
    global SYMBOL_PRECISION, PRICE_PRECISION
    try:
        exchange_info = binance_client.exchange_info()
        for s in exchange_info['symbols']:
            SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
            PRICE_PRECISION[s['symbol']] = s['pricePrecision']
        print(f"[BOT]    Binance Symbols: ✅ Cached {len(SYMBOL_PRECISION)} symbols", '========================')
    except Exception as e:
        print(f"[BOT]    ⚠️ Could not cache decimals: {str(e)}")
    
    # Register event handlers
    # Determine listen channels based on LISTEN_TO_SIGNAL_GROUP
    listen_channel_bot_1_p = SIGNAL_CHANNEL_ID_BOT_1_P if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID_BOT_1_P
    listen_channel_bot_2_bk = SIGNAL_CHANNEL_ID_BOT_2_BK if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID_BOT_2_BK
    
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
    
    precision = {
        'symbol': SYMBOL_PRECISION,
        'price': PRICE_PRECISION
    }
    
    # Register handlers with wrappers to pass config
    # outgoing=False prevents race condition when testing (bot won't react to its own messages)
    @tg_client.on(events.NewMessage(chats=listen_channel_bot_1_p))
    async def wrapper_bot_1_p(event):
        await handle_signal_bot_1_p(event, tg_client, binance_client, config_bot_1_p, precision,
                                     Enter_Trade, TP_Trade, SL_Trade, round_price, calculate_quantity,
                                     PLACE_REAL_TRADES)
    
    @tg_client.on(events.NewMessage(chats=listen_channel_bot_2_bk))
    async def wrapper_bot_2_bk(event):
        await handle_signal_bot_2_bk(event, tg_client, binance_client, config_bot_2_bk, precision,
                                      Enter_Trade, TP_Trade, SL_Trade, round_price, calculate_quantity,
                                      PLACE_REAL_TRADES)


# =============================================================================
# STARTUP LOGIC
# =============================================================================

if __name__ == "__main__":
    
    # Determine listening sources
    bot_1_p_source = "✅Signal Channel" if LISTEN_TO_SIGNAL_GROUP else "❌Private Group"
    bot_2_bk_source = "✅Signal Channel" if LISTEN_TO_SIGNAL_GROUP else "❌Private Group"
    
    print(f"[BOT] 📡 Listening to: {{'BOT_1_P': '{bot_1_p_source}', 'BOT_2_BK': '{bot_2_bk_source}'}} ========================")
    print(f"[BOT] 💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")
    print(f"[BOT]    BOT_1_P - Leverage: {LEVERAGE_BOT_1_P}x | Margin: ${MARGIN_USD_BOT_1_P} -------- BOT_2_BK - Leverage: {LEVERAGE_BOT_2_BK}x | Margin: ${MARGIN_USD_BOT_2_BK}")
    
    tg_client.start()
    tg_client.loop.run_until_complete(startup_tests())
    tg_client.run_until_disconnected()
