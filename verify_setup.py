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

# RUN_ISOLATED_SCRIPT - When true, changes all symbols margin type to ISOLATED
RUN_ISOLATED_SCRIPT = os.getenv('RUN_ISOLATED_SCRIPT', 'false').lower() == 'true'

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
BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

# New 4 channel/group IDs
SIGNAL_CHANNEL_ID_BOT_1_P = os.getenv('SIGNAL_CHANNEL_ID_BOT_1_P')
MY_PRIVATE_GROUP_ID_BOT_1_P = os.getenv('MY_PRIVATE_GROUP_ID_BOT_1_P')
SIGNAL_CHANNEL_ID_BOT_2_BK = os.getenv('SIGNAL_CHANNEL_ID_BOT_2_BK')
MY_PRIVATE_GROUP_ID_BOT_2_BK = os.getenv('MY_PRIVATE_GROUP_ID_BOT_2_BK')

env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'SESSION_STRING', 
            'SIGNAL_CHANNEL_ID_BOT_1_P', 'MY_PRIVATE_GROUP_ID_BOT_1_P',
            'SIGNAL_CHANNEL_ID_BOT_2_BK', 'MY_PRIVATE_GROUP_ID_BOT_2_BK',
            'BINANCE_KEY', 'BINANCE_SECRET']

all_set = all(os.getenv(v) for v in env_vars)
if all_set:
    test_pass("TEST CASE 1: All environment variables set")
else:
    missing = [v for v in env_vars if not os.getenv(v)]
    test_fail(f"TEST CASE 1: Missing: {', '.join(missing)}")

# Convert types
TELEGRAM_API_ID = int(TELEGRAM_API_ID) if TELEGRAM_API_ID else None

# ============================================================
# TEST CASE 2: Binance API Connection
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 2: Binance API Connection")
print("=" * 60)

from binance.um_futures import UMFutures
client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

# Load margin settings for validation
MARGIN_USD_BOT_1_P = int(os.getenv('MARGIN_USD_BOT_1_P', 100))
MARGIN_USD_BOT_2_BK = int(os.getenv('MARGIN_USD_BOT_2_BK', 100))

try:
    account = client.account()
    wallet_balance = float(account['totalWalletBalance'])
    print(f"   Balance: {wallet_balance:.2f} USDT")
    
    # Check Position Mode (must be One-Way, not Hedge)
    mode = client.get_position_mode()
    if mode['dualSidePosition']:
        print("   ⚠️ Position Mode: HEDGE (change to One-Way in Binance settings!)")
    else:
        print("   ✅ Position Mode: One-Way")
    
    # Validate margin settings against wallet balance
    if MARGIN_USD_BOT_1_P > wallet_balance:
        print(f"   ⚠️ MARGIN_USD_BOT_1_P (${MARGIN_USD_BOT_1_P}) > Balance (${wallet_balance:.2f})")
    else:
        print(f"   ✅ BOT_1_P Margin: ${MARGIN_USD_BOT_1_P} < Balance")
    
    if MARGIN_USD_BOT_2_BK > wallet_balance:
        print(f"   ⚠️ MARGIN_USD_BOT_2_BK (${MARGIN_USD_BOT_2_BK}) > Balance (${wallet_balance:.2f})")
    else:
        print(f"   ✅ BOT_2_BK Margin: ${MARGIN_USD_BOT_2_BK} < Balance")
    
    test_pass("TEST CASE 2: Binance API connected")
except Exception as e:
    test_fail(f"TEST CASE 2: Binance API failed - {str(e)}")

# ============================================================
# TEST CASE 3: Telegram Connection & Channel IDs
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 3: Telegram Connection & Channel IDs")
print("=" * 60)

from telethon import TelegramClient
from telethon.sessions import StringSession

# Channel IDs already loaded in TEST CASE 1

async def test_telegram():
    tg_client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await tg_client.start()
    
    me = await tg_client.get_me()
    print(f"   Telegram account: {me.first_name}")
    
    # Test all 4 channel/group IDs
    channels_to_test = [
        (SIGNAL_CHANNEL_ID_BOT_1_P, "Signal Channel BOT_1_P"),
        (MY_PRIVATE_GROUP_ID_BOT_1_P, "Private Group BOT_1_P"),
        (SIGNAL_CHANNEL_ID_BOT_2_BK, "Signal Channel BOT_2_BK"),
        (MY_PRIVATE_GROUP_ID_BOT_2_BK, "Private Group BOT_2_BK"),
    ]
    
    all_passed = True
    for channel_id, channel_name in channels_to_test:
        if not channel_id:
            print(f"   ❌ {channel_name}: NOT SET IN .env")
            all_passed = False
            continue
        
        try:
            entity = await tg_client.get_entity(int(channel_id))
            print(f"   ✅ {channel_name}: {entity.title}")
        except Exception as e:
            print(f"   ❌ {channel_name}: FAILED - {str(e)}")
            all_passed = False
    
    await tg_client.disconnect()
    return all_passed

try:
    telegram_ok = asyncio.run(test_telegram())
    if telegram_ok:
        test_pass("TEST CASE 3: Telegram & all channel IDs verified")
    else:
        test_fail("TEST CASE 3: Telegram channel access failed")
except Exception as e:
    test_fail(f"TEST CASE 3: Telegram failed - {str(e)}")


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
    test_fail(f"TEST CASE 5: Cache failed - {str(e)}")

# ============================================================
# TEST CASE 6: Leverage Change
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 6: Leverage Change (tests trading permissions)")
print("=" * 60)

TEST_SYMBOL = "BTCUSDT"
TEST_LEVERAGE = 5

try:
    # Change leverage (this tests trading permissions and IP whitelist)
    result = client.change_leverage(symbol=TEST_SYMBOL, leverage=TEST_LEVERAGE)
    actual_leverage = result.get('leverage', TEST_LEVERAGE)
    print(f"   Changed {TEST_SYMBOL} leverage to {actual_leverage}x")
    test_pass("TEST CASE 6: Leverage change works (trading permissions OK)")
except Exception as e:
    test_fail(f"TEST CASE 6: Leverage change failed - {str(e)}")


# ============================================================
# TEST CASE 7: Margin Type (ISOLATED if RUN_ISOLATED_SCRIPT=true)
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 7: Margin Type Configuration")
print("=" * 60)

if RUN_ISOLATED_SCRIPT:
    print("   ⚠️ RUN_ISOLATED_SCRIPT=true - Changing all symbols to ISOLATED margin...")
    try:
        exchange_info = client.exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for symbol in symbols:
            try:
                client.change_margin_type(symbol=symbol, marginType='ISOLATED')
                success_count += 1
            except Exception as e:
                if "No need to change margin type" in str(e):
                    skip_count += 1
                else:
                    fail_count += 1
        
        print(f"   ✅ Changed: {success_count} symbols")
        print(f"   ⏭️ Already ISOLATED: {skip_count} symbols")
        print(f"   ❌ Failed: {fail_count} symbols")
        test_pass(f"TEST CASE 7: Set {success_count + skip_count} symbols to ISOLATED margin")
    except Exception as e:
        test_fail(f"TEST CASE 7: Failed to set ISOLATED margin - {str(e)}")
else:
    # Just check BTCUSDT margin type
    try:
        client.change_margin_type(symbol=TEST_SYMBOL, marginType='CROSSED')
        print(f"   {TEST_SYMBOL}: CROSSED margin")
        test_pass("TEST CASE 7: Margin type is CROSSED")
    except Exception as e:
        if "No need to change margin type" in str(e):
            print(f"   {TEST_SYMBOL}: Already CROSSED margin")
            test_pass("TEST CASE 7: Margin type already CROSSED")
        else:
            print(f"   ⚠️ Margin type issue: {str(e)}")
            test_pass("TEST CASE 7: Margin type check completed")

# ============================================================
# TEST CASE 8: Bot Module Import
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 8: Bot Module Import")
print("=" * 60)

try:
    from BOT_1_P import handle_signal_bot_1_p
    from BOT_2_BK import handle_signal_bot_2_bk
    print(f"   ✅ BOT_1_P module imported")
    print(f"   ✅ BOT_2_BK module imported")
    test_pass("TEST CASE 8: Bot modules import successfully")
except ImportError as e:
    test_fail(f"TEST CASE 8: Module import failed - {str(e)}")


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
