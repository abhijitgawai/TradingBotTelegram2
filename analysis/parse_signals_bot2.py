"""
Parse and filter BOT_2_BK signals from fetched messages.
Validates signals and exports to Excel.
"""
import re
from datetime import datetime
from openpyxl import Workbook

# Input/Output files
INPUT_FILE = "analysis/data/bot2_messages.txt"
OUTPUT_FILE = "analysis/data/bot2_signals.xlsx"

def parse_signal(text):
    """
    Parse BOT_2_BK signal format.
    Required fields: Symbol, Side (LONG/SHORT), Entry, Target 1, StopLoss
    Returns dict if valid, None if invalid.
    """
    # 1. Symbol: #COINNAME
    symbol_match = re.search(r'#(\w+)', text)
    if not symbol_match:
        return None
    symbol = symbol_match.group(1).upper() + "USDT"
    
    # 2. Side: LONG or SHORT
    side = None
    text_upper = text.upper()
    if "LONG" in text_upper:
        side = "LONG"
    elif "SHORT" in text_upper:
        side = "SHORT"
    if not side:
        return None
    
    # 3. Entry: Entry: X.XX (first number)
    price_match = re.search(r'Entry:\s*([\d.]+)', text)
    if not price_match:
        return None
    entry = float(price_match.group(1))
    
    # 4. TP1: Target 1: X.XX
    tp1_match = re.search(r'Target 1:\s*([\d.]+)', text)
    if not tp1_match:
        return None
    tp1 = float(tp1_match.group(1))
    
    # 5. StopLoss: StopLoss: X.XX
    sl_match = re.search(r'StopLoss:\s*([\d.]+)', text)
    if not sl_match:
        return None
    sl = float(sl_match.group(1))
    
    # Optional: TP2-TP6
    tps = [tp1]
    for i in range(2, 7):
        tp_match = re.search(rf'Target {i}:\s*([\d.]+)', text)
        if tp_match:
            tps.append(float(tp_match.group(1)))
        else:
            tps.append(None)
    
    return {
        'symbol': symbol,
        'side': side,
        'entry': entry,
        'tp1': tps[0],
        'tp2': tps[1] if len(tps) > 1 else None,
        'tp3': tps[2] if len(tps) > 2 else None,
        'tp4': tps[3] if len(tps) > 3 else None,
        'tp5': tps[4] if len(tps) > 4 else None,
        'tp6': tps[5] if len(tps) > 5 else None,
        'sl': sl
    }

def main():
    print("Parsing BOT_2_BK signals...")
    
    # Read messages
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by separator
    messages = content.split('=' * 50)
    
    # Parse signals
    signals = []
    for msg in messages:
        msg = msg.strip()
        if not msg:
            continue
        
        # Extract timestamp
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', msg)
        if not timestamp_match:
            continue
        timestamp = timestamp_match.group(1)
        
        # Extract text after timestamp
        text = msg[msg.find(']')+1:].strip()
        
        # Parse signal
        signal = parse_signal(text)
        if signal:
            signal['datetime'] = timestamp
            signals.append(signal)
    
    print(f"Found {len(signals)} valid signals out of {len(messages)} messages")
    
    # Export to Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "BOT_2_BK Signals"
    
    # Header
    headers = ['DateTime', 'Symbol', 'Side', 'Entry', 'TP1', 'TP2', 'TP3', 'TP4', 'TP5', 'TP6', 'SL']
    ws.append(headers)
    
    # Data
    for s in signals:
        ws.append([
            s['datetime'],
            s['symbol'],
            s['side'],
            s['entry'],
            s['tp1'],
            s['tp2'],
            s['tp3'],
            s['tp4'],
            s['tp5'],
            s['tp6'],
            s['sl']
        ])
    
    wb.save(OUTPUT_FILE)
    print(f"✅ Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
