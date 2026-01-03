"""
Verify Setup - Complete Test Suite for Trading Bot
Run this single file to verify all components before deploying.

Usage: python verify_setup.py
"""
import os
import re
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Track test results
PASSED = 0
FAILED = 0

def test_pass(msg):
    global PASSED
    PASSED += 1
    print(f"✅ {msg}")

def test_fail(msg):
    global FAILED
    FAILED += 1
    print(f"❌ {msg}")

print("=" * 60)
print("🧪 TRADING BOT - VERIFY SETUP")
print("=" * 60)

# ============================================================
# TEST CASE 1: Environment Variables
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 1: Environment Variables")
print("=" * 60)

def mask(val, show=4):
    if not val: return "NOT SET"
    return val[:show] + "*" * min(len(val) - show, 10) if len(val) > show else val

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
SIGNAL_CHANNEL_ID = os.getenv('SIGNAL_CHANNEL_ID')
MY_PRIVATE_GROUP_ID = os.getenv('MY_PRIVATE_GROUP_ID')
BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')
LEVERAGE = os.getenv('LEVERAGE', '5')
MARGIN_USD = os.getenv('MARGIN_USD', '100')

env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'SESSION_STRING', 
            'SIGNAL_CHANNEL_ID', 'MY_PRIVATE_GROUP_ID', 'BINANCE_KEY', 'BINANCE_SECRET']

all_set = all(os.getenv(v) for v in env_vars)
if all_set:
    test_pass("TEST CASE 1: All environment variables set")
else:
    test_fail("TEST CASE 1: Missing environment variables")

# Check -100 format
if SIGNAL_CHANNEL_ID and SIGNAL_CHANNEL_ID.startswith('-100'):
    print(f"   ✅ SIGNAL_CHANNEL_ID uses -100 format")
else:
    print(f"   ⚠️ SIGNAL_CHANNEL_ID should start with -100")

if MY_PRIVATE_GROUP_ID and MY_PRIVATE_GROUP_ID.startswith('-100'):
    print(f"   ✅ MY_PRIVATE_GROUP_ID uses -100 format")
else:
    print(f"   ⚠️ MY_PRIVATE_GROUP_ID should start with -100")

# Convert types
TELEGRAM_API_ID = int(TELEGRAM_API_ID) if TELEGRAM_API_ID else None
SIGNAL_CHANNEL_ID = int(SIGNAL_CHANNEL_ID) if SIGNAL_CHANNEL_ID else None
MY_PRIVATE_GROUP_ID = int(MY_PRIVATE_GROUP_ID) if MY_PRIVATE_GROUP_ID else None
LEVERAGE = int(LEVERAGE)
MARGIN_USD = int(MARGIN_USD)

# ============================================================
# TEST CASE 2: Binance API Connection
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 2: Binance API Connection")
print("=" * 60)

from binance.um_futures import UMFutures
client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

try:
    account = client.account()
    print(f"   Balance: {account['totalWalletBalance']} USDT")
    test_pass("TEST CASE 2: Binance API connected")
except Exception as e:
    test_fail(f"TEST CASE 2: Binance API failed - {str(e)[:40]}")

# ============================================================
# TEST CASE 3: Telegram Connection
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 3: Telegram Connection")
print("=" * 60)

from telethon import TelegramClient
from telethon.sessions import StringSession

async def test_telegram():
    tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await tg_client.start()
    
    me = await tg_client.get_me()
    print(f"   Connected as: {me.first_name}")
    
    # Test Signal Channel
    try:
        entity = await tg_client.get_entity(SIGNAL_CHANNEL_ID)
        print(f"   Signal Channel: {entity.title}")
        signal_ok = True
    except:
        print(f"   Signal Channel: Failed")
        signal_ok = False
    
    # Test Private Group
    try:
        entity = await tg_client.get_entity(MY_PRIVATE_GROUP_ID)
        print(f"   Private Group: {entity.title}")
        private_ok = True
    except:
        print(f"   Private Group: Failed")
        private_ok = False
    
    await tg_client.disconnect()
    return signal_ok and private_ok

try:
    telegram_ok = asyncio.run(test_telegram())
    if telegram_ok:
        test_pass("TEST CASE 3: Telegram connected")
    else:
        test_fail("TEST CASE 3: Telegram channel access failed")
except Exception as e:
    test_fail(f"TEST CASE 3: Telegram failed - {str(e)[:40]}")

# ============================================================
# TEST CASE 4: Signal Parsing
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 4: Signal Parsing")
print("=" * 60)

test_signal = """📥 #DOGE | Open Long
Current price: 0.31500
TP 1: 0.31800 - Probability 95%
"""

symbol_match = re.search(r'#(\w+)', test_signal)
side_found = "Open Long" in test_signal or "Open Short" in test_signal
price_match = re.search(r'Current price: ([\d.]+)', test_signal)
tp1_match = re.search(r'TP 1: ([\d.]+)', test_signal)

if symbol_match and side_found and price_match and tp1_match:
    print(f"   Symbol: {symbol_match.group(1)}USDT")
    print(f"   Entry: {price_match.group(1)}, TP1: {tp1_match.group(1)}")
    test_pass("TEST CASE 4: Signal parsing works")
else:
    test_fail("TEST CASE 4: Signal parsing failed")

# ============================================================
# TEST CASE 5: Symbol Precision Cache
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 5: Symbol Precision Cache")
print("=" * 60)

try:
    start = time.time()
    exchange_info = client.exchange_info()
    PRECISION = {s['symbol']: s['quantityPrecision'] for s in exchange_info['symbols']}
    elapsed = (time.time() - start) * 1000
    print(f"   Cached {len(PRECISION)} symbols in {elapsed:.0f}ms")
    print(f"   DOGEUSDT precision: {PRECISION.get('DOGEUSDT', 'N/A')} decimals")
    test_pass("TEST CASE 5: Symbol precision cached")
except Exception as e:
    test_fail(f"TEST CASE 5: Cache failed - {str(e)[:40]}")

# ============================================================
# TEST CASE 6: Margin & Leverage
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 6: Margin & Leverage")
print("=" * 60)

TEST_SYMBOL = "DOGEUSDT"
try:
    # Set Isolated
    try:
        client.change_margin_type(symbol=TEST_SYMBOL, marginType='ISOLATED')
        print(f"   Changed to ISOLATED")
    except Exception as e:
        if 'No need to change' in str(e):
            print(f"   Already ISOLATED")
    
    # Set Leverage
    result = client.change_leverage(symbol=TEST_SYMBOL, leverage=LEVERAGE)
    print(f"   Leverage: {LEVERAGE}x")
    test_pass("TEST CASE 6: Margin & Leverage set")
except Exception as e:
    test_fail(f"TEST CASE 6: Failed - {str(e)[:40]}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("🏁 TEST SUMMARY")
print("=" * 60)
print(f"\n   ✅ PASSED: {PASSED}")
print(f"   ❌ FAILED: {FAILED}")
print(f"   📊 TOTAL:  {PASSED + FAILED}")

if FAILED == 0:
    print("\n🎉 All tests passed! Bot is ready to trade.")
else:
    print(f"\n⚠️ {FAILED} test(s) failed. Please fix before deploying.")

print("\nRun 'python bot.py' to start the bot.\n")
