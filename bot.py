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
ISTESTING = os.getenv('ISTESTING', 'false').lower() == 'true'


def normalize_telegram_id(chat_id):
    """Convert -100XXXXXX format to -XXXXXX (Telethon uses raw IDs)"""
    id_str = str(chat_id)
    if id_str.startswith('-100'):
        return int('-' + id_str[4:])
    return int(chat_id)


# Load and normalize channel IDs
SIGNAL_CHANNEL_ID = normalize_telegram_id(os.getenv('SIGNAL_CHANNEL_ID'))
MY_PRIVATE_GROUP_ID = normalize_telegram_id(os.getenv('MY_PRIVATE_GROUP_ID'))

# Testing mode - use private group as signal source
if ISTESTING:
    SIGNAL_CHANNEL_ID = MY_PRIVATE_GROUP_ID
    print(f"🧪 TESTING MODE: Listening to group {SIGNAL_CHANNEL_ID}")
else:
    print(f"🚀 PRODUCTION MODE: Listening to channel {SIGNAL_CHANNEL_ID}")  

# Initialize Clients
tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
binance_client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

@tg_client.on(events.NewMessage(chats=SIGNAL_CHANNEL_ID))
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
        # Calculate Quantity
        quantity = round((MARGIN_USD * LEVERAGE) / entry_price, 1)
        print(f"   📌 Quantity: {quantity}")

        if not ISTESTING:
            print(f"   🔄 Placing real orders on Binance...")
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

            print(f"   📤 Sending success message...")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🚀 Trade Placed: {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}")
        else:
            print(f"   🧪 TEST MODE - Skipping Binance, sending test message...")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"🚀 Test Trade Placed: {symbol} {side}\nEntry: {entry_price}\nTP1: {tp1_price}")

    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"⚠️ Binance Error for {symbol}: {str(e)}")

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    print("Bot is starting...")
    tg_client.start()
    print("Bot is listening...")
    tg_client.run_until_disconnected()

