from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    # This is what you will see when you visit your Render/Railway URL
    return "Trading Bot is Online and Listening to Telegram!"

def run():
    # Use the Port assigned by the cloud provider, or 8080 locally
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # We run this in a separate thread so it doesn't stop the Telegram bot
    t = Thread(target=run)
    t.daemon = True 
    t.start()