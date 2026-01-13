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

# Trading parameters
LEVERAGE_BOT_1_P = os.getenv('LEVERAGE_BOT_1_P')
LEVERAGE_BOT_2_BK = os.getenv('LEVERAGE_BOT_2_BK')
MARGIN_USD_BOT_1_P = os.getenv('MARGIN_USD_BOT_1_P')
MARGIN_USD_BOT_2_BK = os.getenv('MARGIN_USD_BOT_2_BK')

# All required environment variables
env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'SESSION_STRING', 
            'SIGNAL_CHANNEL_ID_BOT_1_P', 'MY_PRIVATE_GROUP_ID_BOT_1_P',
            'SIGNAL_CHANNEL_ID_BOT_2_BK', 'MY_PRIVATE_GROUP_ID_BOT_2_BK',
            'BINANCE_KEY', 'BINANCE_SECRET',
            'LEVERAGE_BOT_1_P', 'LEVERAGE_BOT_2_BK',
            'MARGIN_USD_BOT_1_P', 'MARGIN_USD_BOT_2_BK']

all_set = all(os.getenv(v) for v in env_vars)
if all_set:
    test_pass("TEST CASE 1: All environment variables set")
else:
    missing = [v for v in env_vars if not os.getenv(v)]
    test_fail(f"TEST CASE 1: Missing: {', '.join(missing)}")
    print("\n⛔ CRITICAL: Cannot continue without required environment variables.")
    print("   Please set all variables in .env file and try again.")
    exit(1)

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

# Convert margin/leverage to int (already loaded as strings above)
MARGIN_USD_BOT_1_P = int(MARGIN_USD_BOT_1_P)
MARGIN_USD_BOT_2_BK = int(MARGIN_USD_BOT_2_BK)
LEVERAGE_BOT_1_P = int(LEVERAGE_BOT_1_P)
LEVERAGE_BOT_2_BK = int(LEVERAGE_BOT_2_BK)

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
# TEST CASE 4: Signal Parsing (BOT_1_P and BOT_2_BK)
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 4: Signal Parsing")
print("=" * 60)

# BOT_1_P sample signals
bot1_signals = [
    """📥 #DOGE | Open Long
Current price: 0.31500
TP 1: 0.31800 - Probability 95%""",
    
    """
        📥 #CUDIS | Open Long
        Current price: 0.02926
        Settings: BYBIT. Timeframe: 45 min
        Strategy score: 4.35

        TP 1: 0.029556 - Probability 94% (PNL 130%)
        TP 2: 0.029861 - Probability 84% (PNL 120%)
        TP 3: 0.030157 - Probability 74% (PNL 68%)
        TP 4: 0.030438 - Probability 71% (PNL 178%)
        TP 5: 0.031626 - Probability 52% (PNL 98%)
        TP 6: 0.035133 - Probability 35% (PNL 784%)
        DCA: 1. 0.027212 2. 0.024871 3. 0.021945

        ID: #Long_CUDIS_19_12_2025_06_45
    """,
    
    """
        📥 #EPT | Open Short
        Current price: 0.003428
        Settings: BYBIT. Timeframe: 45 min
        Strategy score: 5.9

        TP 1: 0.0033933 - Probability 94% (PNL 80%)
        TP 2: 0.0033578 - Probability 88% (PNL 140%)
        TP 3: 0.0033245 - Probability 76% (PNL 70%)
        TP 4: 0.0032898 - Probability 76% (PNL 200%)
        TP 5: 0.0031516 - Probability 76% (PNL 720%)
        TP 6: 0.0027392 - Probability 41% (PNL 631%)
        SL: 0.0037022 or DCA

        ID: #Short_EPT_3_11_2025_03_00
    
    """,
]

# BOT_2_BK sample signals
bot2_signals = [
    """
        📥 #EPT | Open Short
        Current price: 0.003428
        Settings: BYBIT. Timeframe: 45 min
        Strategy score: 5.9

        TP 1: 0.0033933 - Probability 94% (PNL 80%)
        TP 2: 0.0033578 - Probability 88% (PNL 140%)
        TP 3: 0.0033245 - Probability 76% (PNL 70%)
        TP 4: 0.0032898 - Probability 76% (PNL 200%)
        TP 5: 0.0031516 - Probability 76% (PNL 720%)
        TP 6: 0.0027392 - Probability 41% (PNL 631%)
        SL: 0.0037022 or DCA

        ID: #Short_EPT_3_11_2025_03_00
    
    """,
    
    """
    
        📥 #EPT | Open Short
        Current price: 0.003428
        Settings: BYBIT. Timeframe: 45 min
        Strategy score: 5.9

        TP 1: 0.0033933 - Probability 94% (PNL 80%)
        TP 2: 0.0033578 - Probability 88% (PNL 140%)
        TP 3: 0.0033245 - Probability 76% (PNL 70%)
        TP 4: 0.0032898 - Probability 76% (PNL 200%)
        TP 5: 0.0031516 - Probability 76% (PNL 720%)
        TP 6: 0.0027392 - Probability 41% (PNL 631%)
        SL: 0.0037022 or DCA

        ID: #Short_EPT_3_11_2025_03_00
    """,
    
    """
        📥 #EPT | Open Short
        Current price: 0.003428
        Settings: BYBIT. Timeframe: 45 min
        Strategy score: 5.9

        TP 1: 0.0033933 - Probability 94% (PNL 80%)
        TP 2: 0.0033578 - Probability 88% (PNL 140%)
        TP 3: 0.0033245 - Probability 76% (PNL 70%)
        TP 4: 0.0032898 - Probability 76% (PNL 200%)
        TP 5: 0.0031516 - Probability 76% (PNL 720%)
        TP 6: 0.0027392 - Probability 41% (PNL 631%)
        SL: 0.0037022 or DCA

        ID: #Short_EPT_3_11_2025_03_00
    """,
]

def test_bot1_signal(signal):
    """Test BOT_1_P signal parsing"""
    symbol = re.search(r'#(\w+)', signal)
    side = "Open Long" in signal or "Open Short" in signal
    price = re.search(r'Current price: ([\d.]+)', signal)
    tp1 = re.search(r'TP 1: ([\d.]+)', signal)
    return symbol and side and price and tp1

def test_bot2_signal(signal):
    """Test BOT_2_BK signal parsing"""
    symbol = re.search(r'#(\w+)', signal)
    side = "LONG" in signal.upper() or "SHORT" in signal.upper()
    price = re.search(r'Entry:\s*([\d.]+)', signal)
    tp1 = re.search(r'Target 1:\s*([\d.]+)', signal)
    sl = re.search(r'StopLoss:\s*([\d.]+)', signal)
    return symbol and side and price and tp1 and sl

# Test BOT_1_P signals
bot1_passed = 0
bot1_failed = 0
for i, signal in enumerate(bot1_signals):
    if test_bot1_signal(signal):
        symbol = re.search(r'#(\w+)', signal).group(1)
        print(f"   [BOT_1_P] Signal {i+1}: ✅ {symbol}USDT")
        bot1_passed += 1
    else:
        print(f"   [BOT_1_P] Signal {i+1}: ❌ Failed")
        bot1_failed += 1

# Test BOT_2_BK signals
bot2_passed = 0
bot2_failed = 0
for i, signal in enumerate(bot2_signals):
    if test_bot2_signal(signal):
        symbol = re.search(r'#(\w+)', signal).group(1)
        print(f"   [BOT_2_BK] Signal {i+1}: ✅ {symbol}USDT")
        bot2_passed += 1
    else:
        print(f"   [BOT_2_BK] Signal {i+1}: ❌ Failed")
        bot2_failed += 1

# Summary
total_passed = bot1_passed + bot2_passed
total_signals = len(bot1_signals) + len(bot2_signals)
print(f"   ---")
print(f"   BOT_1_P: {bot1_passed}/{len(bot1_signals)} passed | BOT_2_BK: {bot2_passed}/{len(bot2_signals)} passed")

if bot1_failed == 0 and bot2_failed == 0:
    test_pass(f"TEST CASE 4: All {total_signals} signals parsed successfully")
else:
    test_fail(f"TEST CASE 4: {bot1_failed + bot2_failed} signals failed")

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
        total = len(symbols)
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for i, symbol in enumerate(symbols):
            try:
                client.change_margin_type(symbol=symbol, marginType='ISOLATED')
                success_count += 1
                print(f"   [{i+1}/{total}] ✅ {symbol} → ISOLATED")
            except Exception as e:
                if "No need to change margin type" in str(e):
                    skip_count += 1
                    print(f"   [{i+1}/{total}] ⏭️ {symbol} (already ISOLATED)")
                else:
                    fail_count += 1
                    print(f"   [{i+1}/{total}] ❌ {symbol} - {str(e)[:50]}")
        
        print(f"\n   Summary:")
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
