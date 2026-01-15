"""
BOT_3_GG Parser - Channel GG (Has Stop Loss + Entry Zone + Multiple Targets)

Signal Format:
📩 #ALGOUSDT 1h | Mid-Term
📉 Short Entry Zone: 0.1308-0.1379
OR
📈 Long Entry Zone: 0.175-0.170

🎯 - Strategy Accuracy:  89.58%
Last 5 signals:  90.0%
...

⏳ - Signal details:
Target 1:  0.1288
Target 2:  0.1269
Target 3:  0.1249
Target 4:  0.1190
_____
🧲Trend-Line: 0.1379
❌Stop-Loss: 0.1399
...
"""

import re


async def handle_signal_bot_3_gg(event, tg_client, binance_client, config, precision,
                                  Enter_Trade, TP_Trade, SL_Trade, round_price, calculate_quantity,
                                  PLACE_REAL_TRADES):
    """
    Handler for BOT_3_GG signal channel.
    Extracts: Symbol, Side, Entry Zone (uses lower bound for Long, upper for Short), 
              Multiple Targets (uses Target 1), Stop-Loss
    """
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
    
    # 1. Extract Symbol (format: #ALGOUSDT or #DYDXUSDT - already has USDT)
    symbol_match = re.search(r'#(\w+USDT)', text)
    if not symbol_match:
        # Try without USDT suffix
        symbol_match = re.search(r'#(\w+)', text)
        if not symbol_match:
            await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Symbol not found")
            print(f"[{bot_id}] ❌ Symbol not found")
            return
        symbol = f"{symbol_match.group(1).upper()}USDT"
    else:
        symbol = symbol_match.group(1).upper()
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
    print(f"   [{bot_id}] 📌 Symbol: {symbol}")
    
    # 2. Extract Side and Entry Zone
    # 📉 Short Entry Zone: 0.1308-0.1379
    # 📈 Long Entry Zone: 0.175-0.170
    side = None
    entry_price = None
    
    short_match = re.search(r'📉\s*Short Entry Zone:\s*([\d.]+)', text)
    long_match = re.search(r'📈\s*Long Entry Zone:\s*([\d.]+)', text)
    
    if short_match:
        side = "SELL"
        entry_price = float(short_match.group(1))
        print(f"   [{bot_id}] 📌 Side: {side}")
    
    if long_match:
        side = "BUY"
        entry_price = float(long_match.group(1))
        print(f"   [{bot_id}] 📌 Side: {side}")
    
    if side is None:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Side not found for {symbol}")
        print(f"[{bot_id}] ❌ Side not found for {symbol}")
        return
    
    print(f"   [{bot_id}] 📌 Entry Price: {entry_price}")
    
    # 3. Extract Targets (use Target 1 as TP)
    # Target 1:  0.1288
    tp1_match = re.search(r'Target 1:\s*([\d.]+)', text)
    if not tp1_match:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Target 1 not found for {symbol}")
        print(f"[{bot_id}] ❌ Target 1 not found for {symbol}")
        return
    tp1_price = float(tp1_match.group(1))
    print(f"   [{bot_id}] 📌 TP1 (Target 1): {tp1_price}")
    
    # 4. Extract Stop-Loss
    # ❌Stop-Loss: 0.1399
    sl_match = re.search(r'❌\s*Stop-Loss:\s*([\d.]+)', text)
    sl_price = None
    if sl_match:
        sl_price = float(sl_match.group(1))
        print(f"   [{bot_id}] 📌 SL: {sl_price}")
    else:
        print(f"   [{bot_id}] ⚠️ SL not found - proceeding without SL")
    
    # 5. Extract additional info (optional, for logging)
    # accuracy_match = re.search(r'Strategy Accuracy:\s*([\d.]+)%', text)
    # if accuracy_match:
    #     accuracy = float(accuracy_match.group(1))
    #     print(f"   [{bot_id}] 📌 Strategy Accuracy: {accuracy}%")
    
    # --- EXECUTION ---
    try:
        # Round prices to valid tick size
        entry_price_rounded = round_price(entry_price, symbol)
        tp1_price_rounded = round_price(tp1_price, symbol)
        sl_price_rounded = round_price(sl_price, symbol) if sl_price else None
        print(f"   [{bot_id}] 📌 Entry (rounded): {entry_price_rounded}, TP1 (rounded): {tp1_price_rounded}, SL (rounded): {sl_price_rounded}")
        
        # Calculate Quantity
        quantity = calculate_quantity(margin_usd, leverage, entry_price_rounded, symbol)
        print(f"   [{bot_id}] 📌 Qty: {quantity}")
        
        print(f"[{bot_id}] ====Executing====")
        
        # Place Entry Order
        entry_success = Enter_Trade(symbol, side, quantity, entry_price_rounded, leverage, bot_id)
        
        if entry_success:
            # Place TP Order
            exit_side = "SELL" if side == "BUY" else "BUY"
            TP_Trade(symbol, exit_side, quantity, tp1_price_rounded, bot_id)
            
            # Place SL Order (if SL price is present)
            if sl_price_rounded:
                SL_Trade(symbol, exit_side, quantity, bot_id, executeSL=True, stop_price=sl_price_rounded)
            else:
                SL_Trade(symbol, exit_side, quantity, bot_id, executeSL=False, stop_price=None)
            
            # Send notification AFTER all trades (wrapped in try-catch)
            try:
                if PLACE_REAL_TRADES:
                    msg = f"[{bot_id}] 🚀 {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}"
                    if sl_price_rounded:
                        msg += f"\nSL: {sl_price_rounded}"
                else:
                    msg = f"[{bot_id}] 🧪 [SIM] {symbol} {side}\nEntry: {entry_price_rounded}\nTP1: {tp1_price_rounded}\nQty: {quantity}"
                    if sl_price_rounded:
                        msg += f"\nSL: {sl_price_rounded}"
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

