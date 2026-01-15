"""
Run this script ONCE locally to generate your SESSION_STRING.
Then copy the output and paste it into your .env file.
"""
import sys
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Add parent directory to path to allow finding .env easily if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load from .env file
load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n" + "="*50)
    print("YOUR SESSION STRING (copy this to .env):")
    print("="*50)
    print(client.session.save())
    print("="*50 + "\n")
