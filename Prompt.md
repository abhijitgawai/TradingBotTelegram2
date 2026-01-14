# Complete Telegram-Binance Trading Bot Prompt

## Project Overview
Build a Python trading bot that:
1. Listens to **multiple Telegram channels** for trading signals
2. Parses signal messages using channel-specific parsers (BOT_1_P, BOT_2_BK, BOT_3_GG)
3. Executes trades on Binance Futures via API (Entry + TP + SL)
4. Sends notifications to corresponding private Telegram groups

---

## Configuration Variables

### Telegram Credentials
| Variable | Description | How to Get |
|----------|-------------|------------|
| `TELEGRAM_API_ID` | Your Telegram app ID (integer) | https://my.telegram.org → API Development Tools |
| `TELEGRAM_API_HASH` | Your Telegram app hash (string) | Same as above |
| `SESSION_STRING` | Encoded Telegram session | Run `python generate_session.py` once locally |

### Binance Credentials
| Variable | Description | How to Get |
|----------|-------------|------------|
| `BINANCE_KEY` | Binance API key | Binance → API Management → Create API |
| `BINANCE_SECRET` | Binance API secret | Same. Enable Futures, disable Withdraw. Whitelist IP! |

### Channel Configuration (Dual Bot)
| Variable | Description | Example |
|----------|-------------|---------|
| `SIGNAL_CHANNEL_ID_BOT_1_P` | Signal channel for BOT_1_P | `-1001234567890` |
| `MY_PRIVATE_GROUP_ID_BOT_1_P` | Private group for BOT_1_P notifications | `-1009876543210` |
| `SIGNAL_CHANNEL_ID_BOT_2_BK` | Signal channel for BOT_2_BK | `-1001234567890` |
| `MY_PRIVATE_GROUP_ID_BOT_2_BK` | Private group for BOT_2_BK notifications | `-1009876543210` |
| `SIGNAL_CHANNEL_ID_BOT_3_GG` | Signal channel for BOT_3_GG | `-1001234567890` |
| `MY_PRIVATE_GROUP_ID_BOT_3_GG` | Private group for BOT_3_GG notifications | `-1009876543210` |

### Trading Parameters (Per Bot)
| Variable | Description | Default |
|----------|-------------|---------|
| `LEVERAGE_BOT_1_P` | Leverage for BOT_1_P | `5` |
| `MARGIN_USD_BOT_1_P` | Margin per trade for BOT_1_P | `100` |
| `LEVERAGE_BOT_2_BK` | Leverage for BOT_2_BK | `5` |
| `MARGIN_USD_BOT_2_BK` | Margin per trade for BOT_2_BK | `100` |
| `LEVERAGE_BOT_3_GG` | Leverage for BOT_3_GG | `5` |
| `MARGIN_USD_BOT_3_GG` | Margin per trade for BOT_3_GG | `100` |

### Testing Switches
| Variable | Values | Purpose |
|----------|--------|---------|
| `LISTEN_TO_SIGNAL_GROUP` | `true`/`false` | `true` = signal channel, `false` = private group |
| `PLACE_REAL_TRADES` | `true`/`false` | `true` = real orders, `false` = simulation |

---

## Signal Formats

### BOT_1_P (Channel P) - No Stop Loss
```
#COINNAME | Open Long
Current price: 0.02926
TP 1: 0.029556 - Probability 94%
```

**Extracted:** Symbol: `DOGEUSDT`, Side: `BUY`, Entry: `0.02926`, TP1: `0.029556`

### BOT_2_BK (Channel BK) - Has Stop Loss
```
#COINNAME/USDT
🟢 LONG (or 🔴 SHORT)
Entry: 0.06527 - 0.06300
Target 1: 0.06592
StopLoss: 0.06180
```

**Extracted:** Symbol: `GMTUSDT`, Side: `BUY`, Entry: `0.06527`, TP1: `0.06592`, SL: `0.06180`

### BOT_3_GG (Channel GG) - Has Entry Zone + Stop Loss
```
📩 #DYDXUSDT 30m | Mid-Term
📈 Long Entry Zone: 0.175-0.170
Target 1:  0.177
❌Stop-Loss: 0.168
```

**Extracted:** Symbol: `DYDXUSDT`, Side: `BUY`, Entry: `0.175` (first number in zone), TP1: `0.177`, SL: `0.168`

---

## Complete bot.py Code

```python
import re
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from binance.um_futures import UMFutures

load_dotenv()

# --- CONFIGURATION ---
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

LEVERAGE = int(os.getenv('LEVERAGE', 5))
MARGIN_USD = int(os.getenv('MARGIN_USD', 100))

LISTEN_TO_SIGNAL_GROUP = os.getenv('LISTEN_TO_SIGNAL_GROUP', 'false').lower() == 'true'
PLACE_REAL_TRADES = os.getenv('PLACE_REAL_TRADES', 'false').lower() == 'true'

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
    
    me = await tg_client.get_me()
    print(f"   Telegram account: {me.first_name}")
    
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
    
    # Test Private Group
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
    
    # Cache symbol precision (tests Binance API)
    global SYMBOL_PRECISION, PRICE_PRECISION
    try:
        exchange_info = binance_client.exchange_info()
        for s in exchange_info['symbols']:
            SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
            PRICE_PRECISION[s['symbol']] = s['pricePrecision']
        print(f"   Binance API: ✅ Cached {len(SYMBOL_PRECISION)} symbols")
    except Exception as e:
        print(f"   ⚠️ Could not cache decimals: {str(e)}")
    
    # Register handler
    global LISTEN_CHANNEL
    LISTEN_CHANNEL = SIGNAL_CHANNEL_ID if LISTEN_TO_SIGNAL_GROUP else MY_PRIVATE_GROUP_ID
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

    # --- EXECUTION ---
    try:
        # Helper function to round price to valid tick size
        def round_price(price, symbol):
            price_decimals = PRICE_PRECISION.get(symbol, 6)
            return round(price, price_decimals)
        
        # Round prices to valid tick size
        entry_price_rounded = round_price(entry_price, symbol)
        tp1_price_rounded = round_price(tp1_price, symbol)
        
        print(f"   📌 Entry (rounded): {entry_price_rounded}, TP1 (rounded): {tp1_price_rounded}")
        
        # Calculate Quantity
        raw_qty = (MARGIN_USD * LEVERAGE) / entry_price_rounded
        decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price_rounded <= 1 else 1)
        quantity = round(raw_qty, decimals)
        if decimals == 0:
            quantity = int(quantity)
        print(f"   📌 Qty: {quantity}")

        if PLACE_REAL_TRADES:
            # Set Leverage
            binance_client.change_leverage(symbol=symbol, leverage=LEVERAGE)

            # Entry LIMIT Order
            binance_client.new_order(
                symbol=symbol, side=side, type='LIMIT',
                timeInForce='GTC', quantity=quantity, price=entry_price_rounded
            )

            # TP LIMIT Order (reduceOnly)
            exit_side = "SELL" if side == "BUY" else "BUY"
            binance_client.new_order(
                symbol=symbol, side=exit_side, type='LIMIT',
                quantity=quantity, price=tp1_price_rounded,
                timeInForce='GTC', reduceOnly="True"
            )

            print(f"   ✅ Orders placed!")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, 
                f"🚀 {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}")
        else:
            print(f"   🧪 SIMULATION")
            await tg_client.send_message(MY_PRIVATE_GROUP_ID, 
                f"🧪 [SIM] {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}")

    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"⚠️ Error for {symbol}: {str(e)}")


if __name__ == "__main__":
    print("===============🤖 BOT CONFIGURATION===============")
    print(f"📡 Listening to: {'✅ Signal Channel' if LISTEN_TO_SIGNAL_GROUP else '❌ Private Group (testing)'}")
    print(f"💰 Real Trades: {'✅ YES' if PLACE_REAL_TRADES else '❌ NO (simulation)'}")
    print(f"📊 Leverage: {LEVERAGE}x | Margin: ${MARGIN_USD}")
    
    tg_client.start()
    tg_client.loop.run_until_complete(startup_tests())
    print("===============================================")
    tg_client.run_until_disconnected()
```

---

## Key Features Implemented

### 1. Dual Precision Caching
```python
SYMBOL_PRECISION = {}  # quantityPrecision - for order quantity
PRICE_PRECISION = {}   # pricePrecision - for tick size validation
```
Both are fetched from Binance on startup and cached for fast lookups.

### 2. Price Tick Size Rounding
```python
def round_price(price, symbol):
    price_decimals = PRICE_PRECISION.get(symbol, 6)
    return round(price, price_decimals)
```
Prevents "Price is not valid" errors from Binance.

### 3. Smart Quantity Calculation
```python
decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price_rounded <= 1 else 1)
```
Handles both cheap coins (SHIB: 0 decimals) and expensive coins (BTC: decimals).

### 4. Channel ID Normalization
```python
norm_id = int('-' + str(SIGNAL_CHANNEL_ID)[4:])
```
Converts `-1001234567890` to `-1234567890` if raw ID fails.

---

## GCP Deployment Commands

```bash
# SSH into GCP VM
gcloud compute ssh tradingbot-vm --zone=us-central1-a

# Service Management
sudo systemctl start tradingbot
sudo systemctl stop tradingbot
sudo systemctl restart tradingbot
sudo systemctl status tradingbot

# View Logs (last 100 lines)
sudo journalctl -u tradingbot -n 100 --no-pager

# Follow logs live
sudo journalctl -u tradingbot -f
```

---

## Testing Flow

1. Set `LISTEN_TO_SIGNAL_GROUP=false`, `PLACE_REAL_TRADES=false`
2. Run `python verify_setup.py` - all tests pass
3. Run `python bot.py` - check startup output
4. Send test signal to private group → verify simulation response
5. Go live: both switches to `true`

---

## Required Files

| File | Purpose |
|------|---------|
| `bot.py` | Main engine - routes signals to parsers, contains trade functions |
| `BOT_1_P.py` | Parser for Channel P signals (no SL) |
| `BOT_2_BK.py` | Parser for Channel BK signals (has SL) |
| `BOT_3_GG.py` | Parser for Channel GG signals (Entry Zone + SL) |
| `verify_setup.py` | Test suite for API connections |
| `generate_session.py` | One-time session string generator |
| `.env` | Configuration (not in git) |
| `requirements.txt` | Dependencies |

## Project Architecture

```
bot.py (Engine)
├── Enter_Trade()      # Place entry LIMIT order
├── TP_Trade()         # Place take profit order
├── SL_Trade()         # Place stop loss order (executeSL param)
├── round_price()      # Round to valid tick size
└── calculate_quantity() # Calculate order quantity

BOT_1_P.py (Parser)
└── handle_signal_bot_1_p()  # Parse Channel P format, no SL

BOT_2_BK.py (Parser)
└── handle_signal_bot_2_bk() # Parse Channel BK format, has SL

BOT_3_GG.py (Parser)
└── handle_signal_bot_3_gg() # Parse Channel GG format, Entry Zone + SL
```

---

## 📝 Important Prompts & Decisions (Conversation History)

This section captures all the key prompts, decisions, and implementation details from development.

### 🔧 Problem 1: Quantity Precision Error
**User Prompt:**
> "Error you can see is Quantity is not valid"

**Root Cause:** Binance requires specific decimal precision for each symbol's quantity.

**Solution:** Cache `quantityPrecision` from `exchange_info()` API on startup:
```python
SYMBOL_PRECISION = {}
for s in exchange_info['symbols']:
    SYMBOL_PRECISION[s['symbol']] = s['quantityPrecision']
```

---

### 🔧 Problem 2: Price Tick Size Error
**User Prompt:**
> "Error: APIError(code=-1111): Precision is over the maximum defined for this asset"

**Root Cause:** Binance has different tick sizes per symbol. A price with too many decimals gets rejected.

**Solution:** Added `PRICE_PRECISION` cache + `round_price()` helper:
```python
PRICE_PRECISION = {}
for s in exchange_info['symbols']:
    PRICE_PRECISION[s['symbol']] = s['pricePrecision']

def round_price(price, symbol):
    price_decimals = PRICE_PRECISION.get(symbol, 6)
    return round(price, price_decimals)
```

---

### 🔧 Problem 3: Smart Fallback for Unknown Symbols
**User Prompt:**
> "Quantity is not valid. For SHIB it should be 0 decimals, for BTC it needs decimals"

**Solution:** Smart fallback based on price level:
```python
decimals = SYMBOL_PRECISION.get(symbol, 0 if entry_price_rounded <= 1 else 1)
```
- If price ≤ 1 (cheap coin like SHIB): assume 0 decimals
- If price > 1 (like BTC): assume 1 decimal
- Best case: use cached precision from Binance

---

### 🔧 Problem 4: Channel ID Not Working
**User Prompt:**
> "Signal Channel: FAILED"

**Root Cause:** Telegram IDs come in different formats:
- Web URL: `-1001234567890`
- API sometimes needs: `-1234567890`

**Solution:** Try raw ID first, then normalize:
```python
try:
    entity = await tg_client.get_entity(SIGNAL_CHANNEL_ID)
except:
    norm_id = int('-' + str(SIGNAL_CHANNEL_ID)[4:])  # Remove "100" prefix
    entity = await tg_client.get_entity(norm_id)
    SIGNAL_CHANNEL_ID = norm_id  # Update global
```

---

### 🔧 Problem 5: Testing Without Real Money
**User Prompt:**
> "I want to test parsing without placing real trades"

**Solution:** Two-switch system in `.env`:
```env
LISTEN_TO_SIGNAL_GROUP=false  # false = listen to private group
PLACE_REAL_TRADES=false       # false = simulation only
```

**Testing Matrix:**
| LISTEN_TO_SIGNAL_GROUP | PLACE_REAL_TRADES | Mode |
|------------------------|-------------------|------|
| false | false | Test parsing in private group, no trades |
| false | true | Real trades from private group (careful!) |
| true | false | Monitor signal channel, simulation only |
| true | true | 🚀 PRODUCTION |

---

### 🔧 Problem 6: Parsing Errors Silent
**User Prompt:**
> "If parsing fails, I want to know about it in my private group"

**Solution:** Send error messages to private group for each failure:
```python
if not symbol_match:
    await tg_client.send_message(MY_PRIVATE_GROUP_ID, "❌ Symbol not found")
    return

if not price_match:
    await tg_client.send_message(MY_PRIVATE_GROUP_ID, f"❌ Price not found for {symbol}")
    return
```

---

### 🔧 Problem 7: Want to See What's Happening
**User Prompt:**
> "Add print statements so I can debug"

**Solution:** Verbose logging at each step:
```python
print(f"✅ Signal detected!")
print("====Signal====")
print(text)
print("---------------")
print(f"   📌 Symbol: {symbol}")
print(f"   📌 Side: {side}")
print(f"   📌 Entry: {entry_price}")
print(f"   📌 Entry (rounded): {entry_price_rounded}")
print(f"   📌 Qty: {quantity}")
```

---

### 🔧 Problem 8: Isolated Margin Mode
**User Prompt:**
> "Use isolated margin mode, not cross margin"

**Solution:** Created `verify_setup.py` with option to set ALL symbols to ISOLATED:
```python
if RUN_ISOLATED_SCRIPT:
    for symbol in all_symbols:
        binance_client.change_margin_type(symbol=symbol, marginType='ISOLATED')
```
Run once with `RUN_ISOLATED_SCRIPT=true`, then set back to `false`.

---

### 🔧 Problem 9: GCP Logs
**User Prompt:**
> "give command for gcp to get last 100 print statements"

**Solution:**
```bash
sudo journalctl -u tradingbot -n 100 --no-pager
```

---

### 🔧 Problem 10: Startup Acts as Test
**User Prompt:**
> "Add precision caching first so startup acts as a small test of Binance API"

**Solution:** `startup_tests()` function that:
1. Tests Telegram connection
2. Tests channel access
3. Caches symbol precision (tests Binance API)
4. Registers event handler

If any step fails, you see the error before bot starts listening.

---

## 📋 Full .env Template

```env
# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
SESSION_STRING=your_session_string

# Binance
BINANCE_KEY=your_binance_key
BINANCE_SECRET=your_binance_secret

# Testing Switches
LISTEN_TO_SIGNAL_GROUP=true
PLACE_REAL_TRADES=false

# BOT 1 (Channel P) - No Stop Loss
SIGNAL_CHANNEL_ID_BOT_1_P=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_1_P=-xxxxxxxxxx
LEVERAGE_BOT_1_P=5
MARGIN_USD_BOT_1_P=100

# BOT 2 (Channel BK) - Has Stop Loss
SIGNAL_CHANNEL_ID_BOT_2_BK=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_2_BK=-xxxxxxxxxx
LEVERAGE_BOT_2_BK=5
MARGIN_USD_BOT_2_BK=100

# BOT 3 (Channel GG) - Has Entry Zone + Stop Loss
SIGNAL_CHANNEL_ID_BOT_3_GG=-100xxxxxxxxxx
MY_PRIVATE_GROUP_ID_BOT_3_GG=-xxxxxxxxxx
LEVERAGE_BOT_3_GG=5
MARGIN_USD_BOT_3_GG=100

# One-time setup (run verify_setup.py with this true)
RUN_ISOLATED_SCRIPT=false
```

---

## 🚀 Deployment Checklist

1. ✅ Generate SESSION_STRING locally
2. ✅ Set up `.env` with all credentials
3. ✅ Run `python verify_setup.py` - all tests pass
4. ✅ Test with `LISTEN_TO_SIGNAL_GROUP=false`, `PLACE_REAL_TRADES=false`
5. ✅ Send test signal to private group
6. ✅ Verify simulation response
7. ✅ Enable signal channel: `LISTEN_TO_SIGNAL_GROUP=true`
8. ✅ Test with simulation on real signals
9. ✅ Go live: `PLACE_REAL_TRADES=true`
10. ✅ Deploy to GCP VM

---

## 📁 Project Structure

```
TradingBotTelegram2/
├── bot.py              # Main engine - trade functions, startup tests
├── BOT_1_P.py          # Parser for Channel P (no SL)
├── BOT_2_BK.py         # Parser for Channel BK (has SL)
├── BOT_3_GG.py         # Parser for Channel GG (Entry Zone + SL)
├── verify_setup.py     # Test suite + isolated margin setup
├── generate_session.py # One-time session generator
├── requirements.txt    # Dependencies
├── .env                # Config (local only, not in git)
├── .gitignore          # Excludes .env and other sensitive files
├── README.md           # Setup & deployment guide
└── Prompt.md           # This file - recreate the bot from scratch
```

