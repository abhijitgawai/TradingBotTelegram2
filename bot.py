import re
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from binance.um_futures import UMFutures

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION (from .env) ---
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

LEVERAGE = int(os.getenv('LEVERAGE', 5))
MARGIN_USD = int(os.getenv('MARGIN_USD', 100))

# --- TESTING CONFIGURATION (2 simple variables) ---
# LISTEN_TO_SIGNAL_GROUP: If true, bot listens to signal channel. If false, listens to private group.
# PLACE_REAL_TRADES: If true, bot places real orders on Binance. If false, only simulates.

LISTEN_TO_SIGNAL_GROUP = os.getenv('LISTEN_TO_SIGNAL_GROUP', 'false').lower() == 'true'
PLACE_REAL_TRADES = os.getenv('PLACE_REAL_TRADES', 'false').lower() == 'true'


def normalize_telegram_id(chat_id):
    """Convert -100XXXXXX format to -XXXXXX (Telethon uses raw IDs)"""
    id_str = str(chat_id)
    if id_str.startswith('-100'):
        return int('-' + id_str[4:])
    return int(chat_id)


# Load and normalize channel IDs
SIGNAL_CHANNEL_ID = normalize_telegram_id(os.getenv('SIGNAL_CHANNEL_ID'))
MY_PRIVATE_GROUP_ID = normalize_telegram_id(os.getenv('MY_PRIVATE_GROUP_ID'))

# Decide which channel to listen to
if LISTEN_TO_SIGNAL_GROUP:
    LISTEN_CHANNEL = SIGNAL_CHANNEL_ID
    source_name = "✅ Signal Channel"
else:
    LISTEN_CHANNEL = MY_PRIVATE_GROUP_ID
    source_name = "❌ Private Group (testing)"

# Print configuration on startup
print("=" * 50)
print("🤖 BOT CONFIGURATION")
print("=" * 50)
print(f"📡 Listening to: {source_name}")
print(f"💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")
print(f"📊 Leverage: {LEVERAGE}x | Margin: ${MARGIN_USD}")
print("=" * 50)

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
binance_client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

# Cache symbol precision from Binance (for accurate quantity rounding)
SYMBOL_PRECISION = {}
try:
    exchange_info = binance_client.exchange_info()
    for s in exchange_info['symbols']:
        SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
    print(f"📋 Cached {len(SYMBOL_PRECISION)} symbol decimals")
except Exception as e:
    print(f"⚠️ Could not cache decimals, using fallback: {str(e)}")


@tg_client.on(events.NewMessage(chats=LISTEN_CHANNEL))
async def handle_new_signal(event):
    print(f"✅ Signal detected! Processing...")
    print("Signal is - " + event.raw_text)
    text = event.raw_text
   
    # 1. Extract Symbol
    symbol_match = re.search(r'#(\w+)', text)
    if symbol_match:
        symbol = f"{symbol_match.group(1).upper()}USDT"
        print(f"   📌 Symbol: {symbol}")
    else:
        print("   ❌ Symbol not found")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, "❌ Error: Could not find Symbol (#) in signal.")
        return

    # 2. Extract Side
    if "Open Long" in text:
        side = "BUY"
        print(f"   📌 Side: {side}")
    elif "Open Short" in text:
        side = "SELL"
        print(f"   📌 Side: {side}")
    else:
        print(f"   ❌ Side not found")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Error: Side (Long/Short) not found for {symbol}.")
        return

    # 3. Extract Entry Price
    price_match = re.search(r'Current price: ([\d.]+)', text)
    if price_match:
        entry_price = float(price_match.group(1))
        print(f"   📌 Entry Price: {entry_price}")
    else:
        print(f"   ❌ Price not found")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Error: Current price missing for {symbol}.")
        return

    # 4. Extract Take Profit 1
    tp1_match = re.search(r'TP 1: ([\d.]+)', text)
    if tp1_match:
        tp1_price = float(tp1_match.group(1))
        print(f"   📌 TP1: {tp1_price}")
    else:
        print(f"   ❌ TP1 not found")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Error: TP 1 missing for {symbol}.")
        return

    # await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"Mesage parsed with no error")

    # --- EXECUTION ---
    try:
        # Calculate Quantity with precision from cache or fallback
        raw_quantity = (MARGIN_USD * LEVERAGE) / entry_price
        
        # Try to get precision from cache, else use price-based fallback
        if symbol in SYMBOL_PRECISION:
            decimals = SYMBOL_PRECISION[symbol]
            precision_source = "API"
        else:
            # Fallback: estimate based on price
            if entry_price <= 1:
                decimals = 0
            else:
                decimals = 1
            precision_source = "fallback"
        
        quantity = round(raw_quantity, decimals)
        if decimals == 0:
            quantity = int(quantity)
        print(f"   📌 Quantity: {quantity} (decimals: {decimals}, source: {precision_source})")

        if PLACE_REAL_TRADES:
            print(f"   🔄 Placing REAL orders on Binance...")
            
            # Set Isolated Margin Mode (uncomment if not using verify_setup.py)
            # try:
            #     binance_client.change_margin_type(symbol=symbol, marginType='ISOLATED')
            #     print(f"   ✅ Margin mode set to ISOLATED")
            # except Exception as e:
            #     if 'No need to change margin type' in str(e):
            #         print(f"   ✅ Already in ISOLATED mode")
            #     else:
            #         print(f"   ⚠️ Margin type warning: {str(e)}")
            
            # Set Leverage
            binance_client.change_leverage(symbol=symbol, leverage=LEVERAGE)

            # Entry LIMIT Order
            binance_client.new_order(
                symbol=symbol, side=side, type='LIMIT',
                timeInForce='GTC', quantity=quantity, price=entry_price
            )

            # TP LIMIT Order
            exit_side = "SELL" if side == "BUY" else "BUY"
            binance_client.new_order(
                symbol=symbol, side=exit_side, type='LIMIT',
                quantity=quantity, price=tp1_price,
                timeInForce='GTC', reduceOnly="True"
            )

            print(f"   ✅ Orders placed successfully!")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🚀 Trade Placed: {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}")
        else:
            print(f"   🧪 SIMULATION - No real trade placed")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🧪 [SIMULATION] {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}\nQty: {quantity}")

    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"⚠️ Binance Error for {symbol}: {str(e)}")

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    print("Bot is starting...")
    tg_client.start()
    print("Bot is listening...")
    tg_client.run_until_disconnected()

