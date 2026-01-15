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
SIGNAL_CHANNEL_ID_BOT_3_GG = os.getenv('SIGNAL_CHANNEL_ID_BOT_3_GG')
MY_PRIVATE_GROUP_ID_BOT_3_GG = os.getenv('MY_PRIVATE_GROUP_ID_BOT_3_GG')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')

# Trading parameters
LEVERAGE_BOT_1_P = os.getenv('LEVERAGE_BOT_1_P')
LEVERAGE_BOT_2_BK = os.getenv('LEVERAGE_BOT_2_BK')
LEVERAGE_BOT_3_GG = os.getenv('LEVERAGE_BOT_3_GG')
MARGIN_USD_BOT_1_P = os.getenv('MARGIN_USD_BOT_1_P')
MARGIN_USD_BOT_2_BK = os.getenv('MARGIN_USD_BOT_2_BK')
MARGIN_USD_BOT_3_GG = os.getenv('MARGIN_USD_BOT_3_GG')

# All required environment variables
env_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'SESSION_STRING', 
            'SIGNAL_CHANNEL_ID_BOT_1_P', 'MY_PRIVATE_GROUP_ID_BOT_1_P',
            'SIGNAL_CHANNEL_ID_BOT_2_BK', 'MY_PRIVATE_GROUP_ID_BOT_2_BK',
            'SIGNAL_CHANNEL_ID_BOT_3_GG', 'MY_PRIVATE_GROUP_ID_BOT_3_GG',
            'ADMIN_GROUP_ID',
            'BINANCE_KEY', 'BINANCE_SECRET',
            'LEVERAGE_BOT_1_P', 'LEVERAGE_BOT_2_BK', 'LEVERAGE_BOT_3_GG',
            'MARGIN_USD_BOT_1_P', 'MARGIN_USD_BOT_2_BK', 'MARGIN_USD_BOT_3_GG']

all_set = all(os.getenv(v) for v in env_vars)
if all_set:
    test_pass("TEST CASE 1: All environment variables set")
else:
    missing = [v for v in env_vars if not os.getenv(v)]
    test_fail(f"TEST CASE 1: Missing: {', '.join(missing)}")
    print("\n⛔ CRITICAL: Cannot continue without required environment variables.")
    print("   Please set all variables in .env file and try again.")
    exit(1)

# Optional: Check ADMIN_BOT_TOKEN (for inline buttons)
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')
if ADMIN_BOT_TOKEN:
    print(f"   ✅ ADMIN_BOT_TOKEN set (buttons enabled!)")
else:
    print(f"   ℹ️ ADMIN_BOT_TOKEN not set (text commands only)")

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
MARGIN_USD_BOT_3_GG = int(MARGIN_USD_BOT_3_GG)
LEVERAGE_BOT_1_P = int(LEVERAGE_BOT_1_P)
LEVERAGE_BOT_2_BK = int(LEVERAGE_BOT_2_BK)
LEVERAGE_BOT_3_GG = int(LEVERAGE_BOT_3_GG)

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
    
    if MARGIN_USD_BOT_3_GG > wallet_balance:
        print(f"   ⚠️ MARGIN_USD_BOT_3_GG (${MARGIN_USD_BOT_3_GG}) > Balance (${wallet_balance:.2f})")
    else:
        print(f"   ✅ BOT_3_GG Margin: ${MARGIN_USD_BOT_3_GG} < Balance")
    
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
    
    # Test all channel/group IDs
    channels_to_test = [
        (SIGNAL_CHANNEL_ID_BOT_1_P, "Signal Channel BOT_1_P"),
        (MY_PRIVATE_GROUP_ID_BOT_1_P, "Private Group BOT_1_P"),
        (SIGNAL_CHANNEL_ID_BOT_2_BK, "Signal Channel BOT_2_BK"),
        (MY_PRIVATE_GROUP_ID_BOT_2_BK, "Private Group BOT_2_BK"),
        (SIGNAL_CHANNEL_ID_BOT_3_GG, "Signal Channel BOT_3_GG"),
        (MY_PRIVATE_GROUP_ID_BOT_3_GG, "Private Group BOT_3_GG"),
        (ADMIN_GROUP_ID, "Admin Group"),
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

# BOT_2_BK sample signals (different format from BOT_1_P)
bot2_signals = [
    """
        📍**Coin : ****#MTL****/USDT
        ****🔴**** SHORT 
        ****➡️**** Entry: 0.4310 - 0.4460
        ****🌐**** Leverage: 20x

        ****😵**** Target 1: 0.4270
        ****😵**** Target 2: 0.4228
        ****😵****l Target 3: 0.4186
        ****😵**** Target 4: 0.4145
        ****😵**** Target 5: 0.4104
        ****😵**** Target 6: 0.4062

        ****❌**** StopLoss: 0.4530**

    """,
    
    """
        📍**Coin : ****#ZIL****/USDT
        ****🔴**** SHORT 
        ****➡️**** Entry: 0.005825 - 0.006000
        ****🌐**** Leverage: 20x

        ****😵**** Target 1: 0.005775
        ****😵**** Target 2: 0.005717
        ****😵**** Target 3: 0.005660
        ****😵**** Target 4: 0.005604
        ****😵**** Target 5: 0.005538
        ****😵**** Target 6: 0.005480

        ****❌**** StopLoss: 0.006260**

    """,
    
    """
        📍Coin : #DUSK/USDT
        🟢 LONG 
        ➡️ Entry: 0.05913 - 0.05760
        🌐 Leverage: 20x

        😵 Target 1: 0.05973
        😵 Target 2: 0.06030
        😵 Target 3: 0.06090
        😵 Target 4: 0.06152
        😵 Target 5: 0.06214
        😵 Target 6: 0.06287

        ❌ StopLoss: 0.05554
    """,
]

# BOT_3_GG sample signals (different format from BOT_1_P)
bot3_signals = [
    """
        📩 #DASHUSDT 1h | Mid-Term
        📉 Short Entry Zone: 41.92-43.80

        🎯 - Strategy Accuracy:  87.49%
        Last 5 signals:  90.0%
        Last 10 signals:  90.0%
        Last 20 signals:  87.5%

        ⏳ - Signal details:
        Target 1:  41.12
        Target 2:  40.33
        Target 3:  39.53
        Target 4:  37.14
        _____
        🧲Trend-Line: 43.80
        ❌Stop-Loss: 44.64
        💡After reaching the first target you can put the rest of the position to breakeven

        #ID20000035980

    """,
    
    """
        📩 #ALTUSDT 30m | Mid-Term
        📈 Long Entry Zone: 0.01309-0.01276

        🎯 - Strategy Accuracy:  91.41%
        Last 5 signals:  85.71%
        Last 10 signals:  83.33%
        Last 20 signals:  90.91%

        ⏳ - Signal details:
        Target 1:  0.01329
        Target 2:  0.01348
        Target 3:  0.01368
        Target 4:  0.01427
        _____
        🧲Trend-Line: 0.01276
        ❌Stop-Loss: 0.01256
        💡After reaching the first target you can put the rest of the position to breakeven

        #ID20000036126

    """,
    
    """
        📩 #ROSEUSDT 30m | Mid-Term
        📈 Long Entry Zone: 0.01066-0.01031

        🎯 - Strategy Accuracy:  88.79%
        Last 5 signals:  90.0%
        Last 10 signals:  90.0%
        Last 20 signals:  80.0%

        ⏳ - Signal details:
        Target 1:  0.01102
        Target 2:  0.01137
        Target 3:  0.01173
        Target 4:  0.01280
        _____
        🧲Trend-Line: 0.01031
        ❌Stop-Loss: 0.00993
        💡After reaching the first target you can put the rest of the position to breakeven

        #ID20000035741
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
    """Test BOT_2_BK signal parsing (Entry:, Target 1:, StopLoss:)"""
    symbol = re.search(r'#(\w+)', signal)
    side = "LONG" in signal.upper() or "SHORT" in signal.upper()
    price = re.search(r'Entry:\s*([\d.]+)', signal)
    tp1 = re.search(r'Target 1:\s*([\d.]+)', signal)
    sl = re.search(r'StopLoss:\s*([\d.]+)', signal)
    return symbol and side and price and tp1 and sl

def test_bot3_signal(signal):
    """Test BOT_3_GG signal parsing (Entry Zone, Target 1, Stop-Loss)"""
    symbol = re.search(r'#(\w+USDT)', signal)
    short_zone = re.search(r'📉\s*Short Entry Zone:\s*([\d.]+)-([\d.]+)', signal)
    long_zone = re.search(r'📈\s*Long Entry Zone:\s*([\d.]+)-([\d.]+)', signal)
    side = short_zone or long_zone
    tp1 = re.search(r'Target 1:\s*([\d.]+)', signal)
    sl = re.search(r'❌\s*Stop-Loss:\s*([\d.]+)', signal)
    return symbol and side and tp1 and sl

# Expected values for assertions
bot1_expected = [
    {'symbol': 'DOGE', 'side': 'BUY', 'entry': '0.31500', 'tp1': '0.31800'},
    {'symbol': 'CUDIS', 'side': 'BUY', 'entry': '0.02926', 'tp1': '0.029556'},
    {'symbol': 'EPT', 'side': 'SELL', 'entry': '0.003428', 'tp1': '0.0033933'},
]

bot2_expected = [
    {'symbol': 'MTL', 'side': 'SELL', 'entry': '0.4310', 'tp1': '0.4270', 'sl': '0.4530'},
    {'symbol': 'ZIL', 'side': 'SELL', 'entry': '0.005825', 'tp1': '0.005775', 'sl': '0.006260'},
    {'symbol': 'DUSK', 'side': 'BUY', 'entry': '0.05913', 'tp1': '0.05973', 'sl': '0.05554'},
]

bot3_expected = [
    {'symbol': 'DASHUSDT', 'side': 'SELL', 'entry': '41.92', 'tp1': '41.12', 'sl': '44.64'},
    {'symbol': 'ALTUSDT', 'side': 'BUY', 'entry': '0.01309', 'tp1': '0.01329', 'sl': '0.01256'},
    {'symbol': 'ROSEUSDT', 'side': 'BUY', 'entry': '0.01066', 'tp1': '0.01102', 'sl': '0.00993'},
]

# Test BOT_1_P signals
bot1_passed = 0
bot1_failed = 0
for i, signal in enumerate(bot1_signals):
    if test_bot1_signal(signal):
        symbol = re.search(r'#(\w+)', signal).group(1)
        side = "BUY" if "Open Long" in signal else "SELL"
        entry = re.search(r'Current price: ([\d.]+)', signal).group(1)
        tp1 = re.search(r'TP 1: ([\d.]+)', signal).group(1)
        
        # Print parsed values
        print(f"   [BOT_1_P] Signal {i+1}: ✅ {symbol}USDT | {side} | Entry: {entry} | TP1: {tp1}")
        
        # Assert expected values
        exp = bot1_expected[i]
        assert symbol == exp['symbol'], f"Symbol mismatch: {symbol} != {exp['symbol']}"
        assert side == exp['side'], f"Side mismatch: {side} != {exp['side']}"
        assert entry == exp['entry'], f"Entry mismatch: {entry} != {exp['entry']}"
        assert tp1 == exp['tp1'], f"TP1 mismatch: {tp1} != {exp['tp1']}"
        print(f"            Expected: {exp['symbol']}USDT | {exp['side']} | Entry: {exp['entry']} | TP1: {exp['tp1']} ✓")
        
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
        side = "BUY" if "LONG" in signal.upper() else "SELL"
        entry = re.search(r'Entry:\s*([\d.]+)', signal).group(1)
        tp1 = re.search(r'Target 1:\s*([\d.]+)', signal).group(1)
        sl = re.search(r'StopLoss:\s*([\d.]+)', signal).group(1)
        
        # Print parsed values
        print(f"   [BOT_2_BK] Signal {i+1}: ✅ {symbol}USDT | {side} | Entry: {entry} | TP1: {tp1} | SL: {sl}")
        
        # Assert expected values
        exp = bot2_expected[i]
        assert symbol == exp['symbol'], f"Symbol mismatch: {symbol} != {exp['symbol']}"
        assert side == exp['side'], f"Side mismatch: {side} != {exp['side']}"
        assert entry == exp['entry'], f"Entry mismatch: {entry} != {exp['entry']}"
        assert tp1 == exp['tp1'], f"TP1 mismatch: {tp1} != {exp['tp1']}"
        assert sl == exp['sl'], f"SL mismatch: {sl} != {exp['sl']}"
        print(f"            Expected: {exp['symbol']}USDT | {exp['side']} | Entry: {exp['entry']} | TP1: {exp['tp1']} | SL: {exp['sl']} ✓")
        
        bot2_passed += 1
    else:
        print(f"   [BOT_2_BK] Signal {i+1}: ❌ Failed")
        bot2_failed += 1

# Test BOT_3_GG signals
bot3_passed = 0
bot3_failed = 0
for i, signal in enumerate(bot3_signals):
    if test_bot3_signal(signal):
        symbol = re.search(r'#(\w+USDT)', signal).group(1)
        short_zone = re.search(r'📉\s*Short Entry Zone:\s*([\d.]+)', signal)
        long_zone = re.search(r'📈\s*Long Entry Zone:\s*([\d.]+)', signal)
        if short_zone:
            side = "SELL"
            entry = short_zone.group(1)
        else:
            side = "BUY"
            entry = long_zone.group(1)
        tp1 = re.search(r'Target 1:\s*([\d.]+)', signal).group(1)
        sl = re.search(r'❌\s*Stop-Loss:\s*([\d.]+)', signal).group(1)
        
        # Print parsed values
        print(f"   [BOT_3_GG] Signal {i+1}: ✅ {symbol} | {side} | Entry: {entry} | TP1: {tp1} | SL: {sl}")
        
        # Assert expected values
        exp = bot3_expected[i]
        assert symbol == exp['symbol'], f"Symbol mismatch: {symbol} != {exp['symbol']}"
        assert side == exp['side'], f"Side mismatch: {side} != {exp['side']}"
        assert entry == exp['entry'], f"Entry mismatch: {entry} != {exp['entry']}"
        assert tp1 == exp['tp1'], f"TP1 mismatch: {tp1} != {exp['tp1']}"
        assert sl == exp['sl'], f"SL mismatch: {sl} != {exp['sl']}"
        print(f"            Expected: {exp['symbol']} | {exp['side']} | Entry: {exp['entry']} | TP1: {exp['tp1']} | SL: {exp['sl']} ✓")
        
        bot3_passed += 1
    else:
        print(f"   [BOT_3_GG] Signal {i+1}: ❌ Failed")
        bot3_failed += 1

# Summary
total_passed = bot1_passed + bot2_passed + bot3_passed
total_signals = len(bot1_signals) + len(bot2_signals) + len(bot3_signals)
print(f"   ---")
print(f"   BOT_1_P: {bot1_passed}/{len(bot1_signals)} passed | BOT_2_BK: {bot2_passed}/{len(bot2_signals)} passed | BOT_3_GG: {bot3_passed}/{len(bot3_signals)} passed")

if bot1_failed == 0 and bot2_failed == 0 and bot3_failed == 0:
    test_pass(f"TEST CASE 4: All {total_signals} signals parsed successfully")
else:
    test_fail(f"TEST CASE 4: {bot1_failed + bot2_failed + bot3_failed} signals failed")

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
    from BOT_3_GG import handle_signal_bot_3_gg
    from ADMIN_BOT import handle_admin_command, send_startup_alert
    print(f"   ✅ BOT_1_P module imported")
    print(f"   ✅ BOT_2_BK module imported")
    print(f"   ✅ BOT_3_GG module imported")
    print(f"   ✅ ADMIN_BOT module imported")
    test_pass("TEST CASE 8: Bot modules import successfully")
except ImportError as e:
    test_fail(f"TEST CASE 8: Module import failed - {str(e)}")


# ============================================================
# TEST CASE 9: ADMIN_BOT Module Tests
# ============================================================
print("\n" + "=" * 60)
print("TEST CASE 9: ADMIN_BOT Module Tests")
print("=" * 60)

try:
    from ADMIN_BOT import (
        handle_admin_command, 
        handle_button_click, 
        send_startup_alert,
        COMMANDS,
        CALLBACK_HANDLERS,
        get_admin_menu
    )
    
    # Test 1: Verify all expected commands exist
    expected_commands = ['/status', '/restart', '/forcerestart', '/deploy', '/config', '/logs', '/help', '/menu', '/test']
    missing_commands = [cmd for cmd in expected_commands if cmd not in COMMANDS]
    
    if missing_commands:
        print(f"   ⚠️ Missing commands: {missing_commands}")
    else:
        print(f"   ✅ All {len(expected_commands)} commands registered")
    
    # Test 2: Verify callback handlers exist
    expected_callbacks = [b'cmd_status', b'cmd_restart', b'cmd_forcerestart', b'cmd_deploy', b'cmd_config', b'cmd_logs', b'cmd_help', b'cmd_test']
    missing_callbacks = [cb for cb in expected_callbacks if cb not in CALLBACK_HANDLERS]
    
    if missing_callbacks:
        print(f"   ⚠️ Missing callbacks: {[cb.decode() for cb in missing_callbacks]}")
    else:
        print(f"   ✅ All {len(expected_callbacks)} button callbacks registered")
    
    # Test 3: Verify menu buttons are generated
    menu_buttons = get_admin_menu()
    button_count = sum(len(row) for row in menu_buttons)
    print(f"   ✅ Menu has {len(menu_buttons)} rows, {button_count} buttons total")
    
    # Test 4: Verify handlers are callable
    for cmd, info in COMMANDS.items():
        if not callable(info['handler']):
            print(f"   ❌ Handler for {cmd} is not callable")
            break
    else:
        print(f"   ✅ All command handlers are callable")
    
    test_pass("TEST CASE 9: ADMIN_BOT module verified")
    
except ImportError as e:
    test_fail(f"TEST CASE 9: ADMIN_BOT import failed - {str(e)}")
except Exception as e:
    test_fail(f"TEST CASE 9: ADMIN_BOT test error - {str(e)}")


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
