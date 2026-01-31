"""
BOT_1_P Parser - Channel P (No Stop Loss)
Parses signals in format:
#COINNAME | Open Long
Current price: 0.02926
TP 1: 0.029556 - Probability 94%
"""

import re


async def handle_signal_bot_1_p(event, tg_client, binance_client, config, precision,
                                 Enter_Trade, TP_Trade, SL_Trade, Place_Bracket_Order, round_price, calculate_quantity,
                                 PLACE_REAL_TRADES):

    bot_id = config['bot_id']
    leverage = config['leverage']
    margin_usd = config['margin_usd']
    private_group_id = config['private_group_id']
    SYMBOL_PRECISION = precision['symbol']
    PRICE_PRECISION = precision['price']
    
    text = event.raw_text
    
    # Skip bot's own messages (prevents race condition during testing)
    if text.startswith(f"[{bot_id}]"):
        print(f"[{bot_id}] ❌ Own message")
        return
    
    print(f"[{bot_id}] ✅ Signal detected!")
    print(f"[{bot_id}] ====Signal====")
    print(text)
    print(f"[{bot_id}] ---------------")
    
    # 1. Extract Symbol
    symbol_match = re.search(r'#(\w+)', text)
    if not symbol_match:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Symbol not found")
        print(f"[{bot_id}] ❌ Symbol not found")
        return
    symbol = symbol_match.group(1).upper()
    if not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    print(f"   [{bot_id}] 📌 Symbol: {symbol}")
    
    # 2. Extract Side
    side = None
    if "Open Long" in text:
        side = "BUY"
    if "Open Short" in text:
        side = "SELL"
    if side is None:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Side not found for {symbol}")
        print(f"[{bot_id}] ❌ Side not found for {symbol}")
        return
    print(f"   [{bot_id}] 📌 Side: {side}")
    
    # 3. Extract Entry Price
    price_match = re.search(r'Current price: ([\d.]+)', text)
    if not price_match:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Price not found for {symbol}")
        print(f"[{bot_id}] ❌ Price not found for {symbol}")
        return
    entry_price = float(price_match.group(1))
    print(f"   [{bot_id}] 📌 Entry: {entry_price}")
    
    # 4. Extract TP1
    tp1_match = re.search(r'TP 1: ([\d.]+)', text)
    if not tp1_match:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ TP1 not found for {symbol}")
        print(f"[{bot_id}] ❌ TP1 not found for {symbol}")
        return
    tp1_price = float(tp1_match.group(1))
    print(f"   [{bot_id}] 📌 TP1: {tp1_price}")
    
    # 5. SL - BOT_1_P does not use Stop Loss
    sl_price = None
    sl_price_rounded = None
    
    # --- EXECUTION ---
    try:
        # Round prices to valid tick size
        entry_price_rounded = round_price(entry_price, symbol)
        tp1_price_rounded = round_price(tp1_price, symbol)
        print(f"   [{bot_id}] 📌 Entry (rounded): {entry_price_rounded}, TP1 (rounded): {tp1_price_rounded}")
        
        # Calculate Quantity
        quantity = calculate_quantity(margin_usd, leverage, entry_price_rounded, symbol)
        print(f"   [{bot_id}] 📌 Qty: {quantity}")
        
        print(f"[{bot_id}] ====Signal====")
        
        # Place Bracket Order (Entry + TP, no SL for BOT_1_P)
        success, result = Place_Bracket_Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price_rounded,
            tp_price=tp1_price_rounded,
            leverage=leverage,
            bot_id=bot_id,
            sl_price=None  # BOT_1_P: No Stop Loss
        )
        
        # Send notification AFTER trade (wrapped in try-catch)
        try:
            if PLACE_REAL_TRADES:
                msg = f"[{bot_id}] 🚀 {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}"
            else:
                msg = f"[{bot_id}] 🧪 [SIM] {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}"
            await tg_client.send_message(private_group_id, msg)
        except Exception as tg_error:
            print(f"   [{bot_id}] ⚠️ Telegram notification failed: {str(tg_error)}")
    
    except Exception as e:
        print(f"   [{bot_id}] ⚠️ Error: {str(e)}")
        try:
            await tg_client.send_message(private_group_id, f"[{bot_id}] ⚠️ Error for {symbol}: {str(e)}")
        except:
            print(f"   [{bot_id}] ⚠️ Telegram notification failed")
            pass  # Don't let notification failure break anything

