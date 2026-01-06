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

# Channel IDs (always use -100 format in .env)
SIGNAL_CHANNEL_ID = int(os.getenv('SIGNAL_CHANNEL_ID'))
MY_PRIVATE_GROUP_ID = int(os.getenv('MY_PRIVATE_GROUP_ID'))

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
binance_client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

# Cache symbol precision (quantity and price)
SYMBOL_PRECISION = {}  # quantityPrecision
PRICE_PRECISION = {}   # pricePrecision (for tick size)


async def startup_tests():
    """Run tests on startup to verify Telegram and Binance access"""
    global SIGNAL_CHANNEL_ID, MY_PRIVATE_GROUP_ID
    
    # Print connected user
    me = await tg_client.get_me()
    print(f"   Telegram account in use: {me.first_name}")
    
    # Test Signal Channel (try raw first, then normalized)
    try:
        entity = await tg_client.get_entity(SIGNAL_CHANNEL_ID)
        print(f"   Signal Channel: {entity.title} (raw)")
    except:
        norm_id = int('-' + str(SIGNAL_CHANNEL_ID)[4:])
        try:
            entity = await tg_client.get_entity(norm_id)
            SIGNAL_CHANNEL_ID = norm_id
            print(f"   Signal Channel: {entity.title} (normalized)")
        except:
            print(f"   ❌ Signal Channel: FAILED")
    
    # Test Private Group (try raw first, then normalized)
    try:
        entity = await tg_client.get_entity(MY_PRIVATE_GROUP_ID)
        print(f"   Private Group: {entity.title} (raw)")
    except:
        norm_id = int('-' + str(MY_PRIVATE_GROUP_ID)[4:])
        try:
            entity = await tg_client.get_entity(norm_id)
            MY_PRIVATE_GROUP_ID = norm_id
            print(f"   Private Group: {entity.title} (normalized)")
        except:
            print(f"   ❌ Private Group: FAILED")
    
    # Cache symbol precision (also tests Binance API connection)
    global SYMBOL_PRECISION, PRICE_PRECISION
    try:
        exchange_info = binance_client.exchange_info()
        for s in exchange_info['symbols']:
            SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
            PRICE_PRECISION[s['symbol']] = s['pricePrecision']
        print(f"   Binance API: ✅ Cached {len(SYMBOL_PRECISION)} symbols (qty + price precision)")
    except Exception as e:
        print(f"   ⚠️ Could not cache decimals: {str(e)}")
    
    # Set LISTEN_CHANNEL after ID detection
    global LISTEN_CHANNEL
    LISTEN_CHANNEL = SIGNAL_CHANNEL_ID if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID
    
    # Register event handler with correct channel
    tg_client.add_event_handler(handle_signal, events.NewMessage(chats=LISTEN_CHANNEL))


async def handle_signal(event):
    print(f"✅ Signal detected!")
    text = event.raw_text
    print("====Signal====")
    print(text)
    print("---------------")
   
    # 1. Extract Symbol
    symbol_match = re.search(r'#(\w+)', text)
    
    if not symbol_match:
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, "❌ Symbol not found")
        return
    symbol = f"{symbol_match.group(1).upper()}USDT"
    print(f"   📌 Symbol: {symbol}")

    # 2. Extract Side
    if "Open Long" in text:
        side = "BUY"
    elif "Open Short" in text:
        side = "SELL"
    else:
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Side not found for {symbol}")
        return
    print(f"   📌 Side: {side}")

    # 3. Extract Entry Price
    price_match = re.search(r'Current price: ([\d.]+)', text)
    if not price_match:
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Price not found for {symbol}")
        return
    entry_price = float(price_match.group(1))
    print(f"   📌 Entry: {entry_price}")

    # 4. Extract TP1
    tp1_match = re.search(r'TP 1: ([\d.]+)', text)
    if not tp1_match:
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ TP1 not found for {symbol}")
        return
    tp1_price = float(tp1_match.group(1))
    print(f"   📌 TP1: {tp1_price}")


    # await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"Mesage parsed with no error")

    # --- EXECUTION ---
    try:
        # Helper function to round price to valid tick size
        def round_price(price, symbol):
            price_decimals = PRICE_PRECISION.get(symbol, 6)  # Default to 6 if not found
            return round(price, price_decimals)
        
        # Round prices to valid tick size
        entry_price_rounded = round_price(entry_price, symbol)
        tp1_price_rounded = round_price(tp1_price, symbol)
        
        print(f"   📌 Entry (rounded): {entry_price_rounded}, 📌 TP1 (rounded): {tp1_price_rounded}")
        # Calculate Quantity
        raw_qty = (MARGIN_USD * LEVERAGE) / entry_price_rounded
        decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price_rounded <= 1 else 1)
        quantity = round(raw_qty, decimals)
        if decimals == 0:
            quantity = int(quantity)
        print(f"   📌 Qty: {quantity}")

        print("====Signal====")

        if PLACE_REAL_TRADES:
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

            # Entry LIMIT Order (using rounded price)
            binance_client.new_order(
                symbol=symbol, side=side, type='LIMIT',
                timeInForce='GTC', quantity=quantity, price=entry_price_rounded
            )

            # TP LIMIT Order (using rounded price)
            exit_side = "SELL" if side == "BUY" else "BUY"
            binance_client.new_order(
                symbol=symbol, side=exit_side, type='LIMIT',
                quantity=quantity, price=tp1_price_rounded,
                timeInForce='GTC', reduceOnly="True"
            )

            print(f"   ✅ Orders placed!")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🚀 {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}")
        else:
            print(f"   🧪 SIMULATION")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🧪 [SIM] {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}")

    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"⚠️ Error for {symbol}: {str(e)}")

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    print("===============🤖 BOT CONFIGURATION===============")
    print(f"📡 Listening to: {'✅ Signal Channel' if LISTEN_TO_SIGNAL_GROUP else '❌ Private Group (testing)'}")
    print(f"💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")
    print(f"📊 Leverage: {LEVERAGE}x | Margin: ${MARGIN_USD}")
    
    
    tg_client.start()
    tg_client.loop.run_until_complete(startup_tests())
    print("===============================================")
    tg_client.run_until_disconnected()
