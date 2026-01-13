"""
Fetch Messages from BOT_1_P Signal Channel
Fetches all messages from last 1 year and saves signals to file.
"""
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

# Config
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('SESSION_STRING')
SIGNAL_CHANNEL_ID = int(os.getenv('SIGNAL_CHANNEL_ID_BOT_1_P'))

# Output file
OUTPUT_FILE = "analysis/data/bot1_messages.txt"

async def fetch_messages():
    client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()
    
    print(f"Connected as: {(await client.get_me()).first_name}")
    
    # Get channel entity
    channel = await client.get_entity(SIGNAL_CHANNEL_ID)
    print(f"Fetching from: {channel.title}")
    
    # Date range: last 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    messages_count = 0
    signals_count = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        async for message in client.iter_messages(channel, offset_date=end_date, reverse=False):
            # Stop if message is older than 1 year
            if message.date.replace(tzinfo=None) < start_date:
                break
            
            messages_count += 1
            
            # Get message text
            text = message.message or ""
            
            # Filter: only messages with # (potential signals)
            if '#' in text:
                signals_count += 1
                # Convert UTC to IST (UTC + 5:30)
                ist_time = message.date + timedelta(hours=5, minutes=30)
                timestamp = ist_time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}]\n{text}\n{'='*50}\n\n")
            
            # Progress indicator
            if messages_count % 500 == 0:
                print(f"  Processed {messages_count} messages, found {signals_count} signals...")
            
            # Rate limit handling
            await asyncio.sleep(0.01)
    
    print(f"\n✅ Done!")
    print(f"   Total messages: {messages_count}")
    print(f"   Signals saved: {signals_count}")
    print(f"   Output: {OUTPUT_FILE}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(fetch_messages())
