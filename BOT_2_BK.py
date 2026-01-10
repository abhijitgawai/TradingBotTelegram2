"""
BOT_2_BK Parser - Channel BK (Has Stop Loss - Future)
TODO: Implement different signal format for this channel.
For now, uses same logic as BOT_1_P.
"""

import re


async def handle_signal_bot_2_bk(event, tg_client, binance_client, config, precision,
                                  Enter_Trade, TP_Trade, SL_Trade, round_price, calculate_quantity,
                                  PLACE_REAL_TRADES):

    bot_id = config['bot_id']
    leverage = config['leverage']
    margin_usd = config['margin_usd']
    private_group_id = config['private_group_id']
    SYMBOL_PRECISION = precision['symbol']
    PRICE_PRECISION = precision['price']
    
    print(f"[{bot_id}] ✅ Signal detected!")
    text = event.raw_text
    print(f"[{bot_id}] ====Signal====")
    print(text)
    print(f"[{bot_id}] ---------------")
    
    # 1. Extract Symbol
    symbol_match = re.search(r'#(\w+)', text)
    if not symbol_match:
        await tg_client.send_message(private_group_id, f"[{bot_id}] ❌ Symbol not found")
        print(f"[{bot_id}] ❌ Symbol not found")
        return
    symbol = f"{symbol_match.group(1).upper()}USDT"
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
    
    # 5. Extract SL (BOT_2_BK specific)
    sl_price = None
    sl_price_rounded = None
    # TODO: Uncomment when signal format is defined
    # sl_match = re.search(r'SL: ([\d.]+)', text)
    # if sl_match:
    #     sl_price = float(sl_match.group(1))
    #     print(f"   [{bot_id}] 📌 SL: {sl_price}")
    
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
        
        # Place Entry Order
        entry_success = Enter_Trade(symbol, side, quantity, entry_price_rounded, leverage, bot_id)
        
        if entry_success:
            # Place TP Order
            exit_side = "SELL" if side == "BUY" else "BUY"
            tp_success = TP_Trade(symbol, exit_side, quantity, tp1_price_rounded, bot_id)
            
            # Place SL Order (if sl_price is defined)
            if sl_price:
                try:
                    sl_price_rounded = round_price(sl_price, symbol)
                    SL_Trade(symbol, exit_side, quantity, bot_id, executeSL=False, stop_price=sl_price_rounded)
                except Exception as e:
                    print(f"   [{bot_id}] ⚠️ SL price error: {str(e)}")
            
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
            print("   [{bot_id}] ⚠️ Telegram notification failed: {str(tg_error)}")
            pass  # Don't let notification failure break anything

