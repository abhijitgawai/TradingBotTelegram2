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

# Which channel to listen
LISTEN_CHANNEL = SIGNAL_CHANNEL_ID if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
binance_client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

# Print config
print("===============🤖 BOT CONFIGURATION===============")
print(f"📡 Listening to: {'Signal Channel' if LISTEN_TO_SIGNAL_GROUP else 'Private Group (testing)'}")
print(f"💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")

# Cache symbol precision from Binance (for accurate quantity rounding)
SYMBOL_PRECISION = {}
try:
    exchange_info = binance_client.exchange_info()
    for s in exchange_info['symbols']:
        SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
    print(f"📋 Cached {len(SYMBOL_PRECISION)} symbol decimals")
except Exception as e:
    print(f"⚠️ Could not cache decimals, using fallback: {str(e)}")

print(f"("===============📊 Leverage: {LEVERAGE}x | Margin: ${MARGIN_USD}("===============")






@tg_client.on(events.NewMessage(chats=LISTEN_CHANNEL))
async def handle_signal(event):
    print(f"✅ Signal detected!")
    text = event.raw_text
    print("====Siginal====")
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
        # Calculate Quantity
        raw_qty = (MARGIN_USD * LEVERAGE) / entry_price
        decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price <= 1 else 1)
        quantity = round(raw_qty, decimals)
        if decimals == 0:
            quantity = int(quantity)
        print(f"   📌 Qty: {quantity}")

        print("====Siginal====")

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

            print(f"   ✅ Orders placed!")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🚀 {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}")
        else:
            print(f"   🧪 SIMULATION")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🧪 [SIM] {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}\nQty: {quantity}")

    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"⚠️ Error for {symbol}: {str(e)}")

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    print("Bot is starting...")
    tg_client.start()
    print("Bot is listening...")
    tg_client.run_until_disconnected()

