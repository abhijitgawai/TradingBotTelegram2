"""
Test suite for Trading Bot functionality.
Run this to verify API connection and bot logic before deploying.

Usage: python verify_setup.py
"""
import os
import re
from dotenv import load_dotenv
from binance.um_futures import UMFutures

load_dotenv()

BINANCE_KEY = os.getenv('BINANCE_KEY')
BINANCE_SECRET = os.getenv('BINANCE_SECRET')

client = UMFutures(key=BINANCE_KEY, secret=BINANCE_SECRET)

# Test configuration
TEST_SYMBOL = "DOGEUSDT"
TEST_LEVERAGE = 5
MARGIN_USD = 100

print("=" * 60)
print("🧪 TRADING BOT TEST SUITE")
print("=" * 60)

# ============================================================
# TEST 1: API Connection
# ============================================================
print("\n-- Test 1: API Connection --")
try:
    account_info = client.account()
    print(f"✅ Connected to Binance Futures")
    print(f"   Total Wallet Balance: {account_info['totalWalletBalance']} USDT")
    print(f"   Available Balance: {account_info['availableBalance']} USDT")
except Exception as e:
    print(f"❌ API Connection Failed: {str(e)}")

# ============================================================
# TEST 2: Margin Type Change (Cross → Isolated)
# ============================================================
print(f"\n-- Test 2: Margin Type Change ({TEST_SYMBOL}) --")
try:
    result = client.change_margin_type(symbol=TEST_SYMBOL, marginType='ISOLATED')
    print(f"✅ Changed to ISOLATED mode")
except Exception as e:
    if 'No need to change margin type' in str(e):
        print(f"✅ Already in ISOLATED mode")
    else:
        print(f"⚠️ Error: {str(e)}")

# ============================================================
# TEST 3: Leverage Change
# ============================================================
print(f"\n-- Test 3: Leverage Change ({TEST_SYMBOL}) --")
try:
    result = client.change_leverage(symbol=TEST_SYMBOL, leverage=TEST_LEVERAGE)
    print(f"✅ Leverage set to {TEST_LEVERAGE}x")
    print(f"   Max Notional: {result['maxNotionalValue']}")
except Exception as e:
    print(f"❌ Leverage Change Failed: {str(e)}")

# ============================================================
# TEST 4: Get Current Price
# ============================================================
print(f"\n-- Test 4: Get Current Price ({TEST_SYMBOL}) --")
try:
    ticker = client.ticker_price(symbol=TEST_SYMBOL)
    current_price = float(ticker['price'])
    print(f"✅ Current Price: ${current_price}")
except Exception as e:
    print(f"❌ Failed to get price: {str(e)}")

# ============================================================
# TEST 5: Smart Quantity Calculation
# ============================================================
print(f"\n-- Test 5: Smart Quantity Calculation --")

test_prices = [
    ("BTCUSDT", 95000.0),    # High price coin
    ("ETHUSDT", 3400.0),     # Mid-high price
    ("SOLUSDT", 185.0),      # Mid price
    ("DOGEUSDT", 0.32),      # Low price
    ("SHIBUSDT", 0.000022),  # Very low price
]

for symbol, price in test_prices:
    raw_quantity = (MARGIN_USD * TEST_LEVERAGE) / price
    if price > 1000:
        decimals = 3
    elif price > 1:
        decimals = 1
    else:
        decimals = 0
    quantity = round(raw_quantity, decimals)
    if decimals == 0:
        quantity = int(quantity)
    print(f"   {symbol}: ${price} → Qty: {quantity} ({decimals} decimals)")

print(f"✅ Quantity calculation tested")

# ============================================================
# TEST 6: Signal Parsing
# ============================================================
print(f"\n-- Test 6: Signal Parsing --")

test_signal = """📥 #DOGE | Open Long
Current price: 0.31500
Settings: BYBIT. Timeframe: 45 min

TP 1: 0.31800 - Probability 95%
TP 2: 0.32000 - Probability 90%
"""

# Parse symbol
symbol_match = re.search(r'#(\w+)', test_signal)
if symbol_match:
    symbol = f"{symbol_match.group(1).upper()}USDT"
    print(f"   Symbol: {symbol} ✅")
else:
    print(f"   Symbol: NOT FOUND ❌")

# Parse side
if "Open Long" in test_signal:
    side = "BUY"
    print(f"   Side: {side} ✅")
elif "Open Short" in test_signal:
    side = "SELL"
    print(f"   Side: {side} ✅")
else:
    print(f"   Side: NOT FOUND ❌")

# Parse price
price_match = re.search(r'Current price: ([\d.]+)', test_signal)
if price_match:
    entry_price = float(price_match.group(1))
    print(f"   Entry Price: {entry_price} ✅")
else:
    print(f"   Entry Price: NOT FOUND ❌")

# Parse TP1
tp1_match = re.search(r'TP 1: ([\d.]+)', test_signal)
if tp1_match:
    tp1_price = float(tp1_match.group(1))
    print(f"   TP1: {tp1_price} ✅")
else:
    print(f"   TP1: NOT FOUND ❌")

print(f"✅ Signal parsing tested")

# ============================================================
# TEST 7: Check Position Mode
# ============================================================
print(f"\n-- Test 7: Position Mode Check --")
try:
    position_mode = client.get_position_mode()
    is_hedge = position_mode.get('dualSidePosition', False)
    mode = "Hedge Mode" if is_hedge else "One-Way Mode"
    print(f"   Current Mode: {mode}")
    if is_hedge:
        print(f"   ⚠️ Warning: Hedge Mode is ON. Bot requires One-Way Mode!")
    else:
        print(f"   ✅ One-Way Mode - Compatible with bot")
except Exception as e:
    print(f"❌ Failed to get position mode: {str(e)}")

# ============================================================
# TEST 8: Symbol Precision Cache (from API)
# ============================================================
print(f"\n-- Test 8: Symbol Precision Cache --")
try:
    import time
    start_time = time.time()
    
    exchange_info = client.exchange_info()
    SYMBOL_PRECISION = {}
    
    for s in exchange_info['symbols']:
        SYMBOL_PRECISION[s['symbol']] = {
            'quantityPrecision': s['quantityPrecision'],
            'pricePrecision': s['pricePrecision'],
        }
    
    elapsed = (time.time() - start_time) * 1000
    
    print(f"✅ Cached {len(SYMBOL_PRECISION)} symbols in {elapsed:.0f}ms")
    
    # Show sample precisions
    sample_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SOLUSDT']
    print(f"\n   Sample Precisions:")
    print(f"   {'Symbol':<12} {'Qty Decimals':<15} {'Price Decimals'}")
    print(f"   {'-'*12} {'-'*15} {'-'*15}")
    for sym in sample_symbols:
        if sym in SYMBOL_PRECISION:
            p = SYMBOL_PRECISION[sym]
            print(f"   {sym:<12} {p['quantityPrecision']:<15} {p['pricePrecision']}")
    
    print(f"\n   ℹ️ This data can be cached at bot startup for instant lookups")
    
except Exception as e:
    print(f"❌ Failed to get exchange info: {str(e)}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("🏁 TEST SUITE COMPLETE")
print("=" * 60)
print("\nIf all tests passed, your bot is ready to trade!")
print("Run 'python bot.py' to start the bot.\n")

# ============================================================
# OPTIONAL: Set ALL Symbols to ISOLATED Mode
# ============================================================
RUN_ISOLATED_SCRIPT = os.getenv('RUN_ISOLATED_SCRIPT', 'false').lower() == 'true'

if RUN_ISOLATED_SCRIPT:
    import time
    print("\n" + "=" * 60)
    print("🔧 SET ALL SYMBOLS TO ISOLATED MODE")
    print("=" * 60)
    
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['contractType'] == 'PERPETUAL']
    print(f"📋 Found {len(symbols)} PERPETUAL symbols")
    print(f"⏱️  Estimated time: ~{len(symbols) * 0.1 / 60:.1f} minutes")
    
    confirm = input("\nType 'yes' to proceed or 'no' to skip: ").strip().lower()
    
    if confirm == 'yes':
        success, already, failed = 0, 0, 0
        for i, sym in enumerate(symbols, 1):
            try:
                client.change_margin_type(symbol=sym, marginType='ISOLATED')
                print(f"[{i}/{len(symbols)}] ✅ {sym}")
                success += 1
            except Exception as e:
                if 'No need to change' in str(e):
                    print(f"[{i}/{len(symbols)}] ⚪ {sym} already ISOLATED")
                    already += 1
                else:
                    print(f"[{i}/{len(symbols)}] ❌ {sym}: {str(e)[:40]}")
                    failed += 1
            time.sleep(0.1)  # Rate limit
        
        print(f"\n📊 Done! Set: {success} | Already: {already} | Failed: {failed}")
    else:
        print("⏭️  Skipped isolated margin setup.")
